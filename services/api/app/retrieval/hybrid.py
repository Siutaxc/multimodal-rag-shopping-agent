"""Text retrieval orchestration with inspectable RRF and bounded reranking."""

from dataclasses import dataclass, replace
from enum import StrEnum
from time import perf_counter
from typing import Any, Protocol

from app.core.settings import Settings
from app.db.models import Product
from app.db.products import ProductFilters
from app.db.search import DenseSearchHit, SearchHit
from app.providers.retrieval import (
    EmbeddingProvider,
    ProviderCircuitOpenError,
    ProviderError,
    ProviderTimeoutError,
    RerankerProvider,
)
from app.retrieval.text_documents import DENSE_DOCUMENT_VERSION, build_dense_document


class SearchMode(StrEnum):
    LEXICAL = "lexical"
    DENSE = "dense"
    RRF = "rrf"
    RERANK = "rerank"


@dataclass(frozen=True)
class RankedCandidate:
    product: Product
    document_version: str
    lexical_rank: int | None = None
    lexical_score: float | None = None
    dense_rank: int | None = None
    dense_score: float | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None


@dataclass(frozen=True)
class SearchExecution:
    mode: str
    items: list[RankedCandidate]
    total: int
    trace: dict[str, Any]


class LexicalRepository(Protocol):
    def search(self, query_text: str, filters: ProductFilters) -> tuple[list[SearchHit], int]: ...


class DenseRepository(Protocol):
    def search(
        self,
        query_vector: list[float],
        filters: ProductFilters,
        *,
        model_name: str,
        model_version: str,
        dimension: int,
        document_version: str,
        limit: int,
    ) -> tuple[list[DenseSearchHit], int]: ...


class HybridSearchService:
    """Run selected ablation paths while preserving hard filters in both repositories."""

    def __init__(
        self,
        lexical_repository: LexicalRepository,
        dense_repository: DenseRepository,
        embedding_provider: EmbeddingProvider,
        reranker_provider: RerankerProvider,
        settings: Settings,
    ) -> None:
        self._lexical = lexical_repository
        self._dense = dense_repository
        self._embedding = embedding_provider
        self._reranker = reranker_provider
        self._settings = settings

    def search(self, query: str, filters: ProductFilters, *, mode: SearchMode) -> SearchExecution:
        trace: dict[str, Any] = {
            "parameters": {
                "lexical_candidate_k": self._settings.lexical_candidate_k,
                "dense_candidate_k": self._settings.dense_candidate_k,
                "fusion_candidate_k": self._settings.fusion_candidate_k,
                "rerank_top_k": self._settings.rerank_top_k,
                "rrf_k": self._settings.rrf_k,
            },
            "models": {
                "embedding": self._embedding.identity.version_key,
                "reranker": self._reranker.identity.version_key,
                "dense_document": DENSE_DOCUMENT_VERSION,
            },
            "degraded_reason": None,
            "channels": {},
            "fusion": [],
            "rerank": [],
            "latency_ms": {},
        }
        started = perf_counter()
        lexical_hits: list[SearchHit] = []
        lexical_total = 0
        if mode in {SearchMode.LEXICAL, SearchMode.RRF, SearchMode.RERANK}:
            channel_started = perf_counter()
            lexical_filters = replace(filters, page=1, page_size=self._settings.lexical_candidate_k)
            lexical_hits, lexical_total = self._lexical.search(query, lexical_filters)
            trace["latency_ms"]["lexical"] = _elapsed_ms(channel_started)
            trace["channels"]["lexical"] = _lexical_trace(lexical_hits)
        if mode == SearchMode.LEXICAL:
            candidates = [
                RankedCandidate(
                    hit.product,
                    hit.document_version,
                    lexical_rank=rank,
                    lexical_score=hit.lexical_score,
                )
                for rank, hit in enumerate(lexical_hits, start=1)
            ]
            trace["latency_ms"]["total"] = _elapsed_ms(started)
            return SearchExecution("postgresql_lexical", candidates, lexical_total, trace)

        dense_hits: list[DenseSearchHit] = []
        dense_total = 0
        try:
            channel_started = perf_counter()
            vectors = self._embedding.embed_texts([query])
            if len(vectors) != 1:
                raise ProviderError("query embedding provider returned the wrong batch size")
            identity = self._embedding.identity
            assert identity.dimension is not None
            dense_hits, dense_total = self._dense.search(
                vectors[0],
                filters,
                model_name=identity.model_name,
                model_version=identity.model_version,
                dimension=identity.dimension,
                document_version=DENSE_DOCUMENT_VERSION,
                limit=self._settings.dense_candidate_k,
            )
            trace["latency_ms"]["dense"] = _elapsed_ms(channel_started)
            trace["channels"]["dense"] = _dense_trace(dense_hits)
        except ProviderCircuitOpenError:
            trace["degraded_reason"] = "embedding_circuit_open"
        except ProviderTimeoutError:
            trace["degraded_reason"] = "embedding_timeout"
        except (ProviderError, ValueError):
            trace["degraded_reason"] = "embedding_error"

        if mode == SearchMode.DENSE and dense_hits:
            candidates = [
                RankedCandidate(
                    hit.product,
                    hit.document_version,
                    dense_rank=rank,
                    dense_score=hit.dense_score,
                )
                for rank, hit in enumerate(dense_hits, start=1)
            ]
            trace["latency_ms"]["total"] = _elapsed_ms(started)
            return SearchExecution("pgvector_dense", candidates, dense_total, trace)
        if mode == SearchMode.DENSE:
            trace["latency_ms"]["total"] = _elapsed_ms(started)
            return SearchExecution("pgvector_dense", [], dense_total, trace)

        fusion_started = perf_counter()
        candidates = reciprocal_rank_fusion(
            lexical_hits,
            dense_hits,
            rrf_k=self._settings.rrf_k,
            limit=self._settings.fusion_candidate_k,
        )
        trace["latency_ms"]["fusion"] = _elapsed_ms(fusion_started)
        trace["fusion"] = _fusion_trace(candidates)
        actual_mode = "hybrid_rrf"

        if mode == SearchMode.RERANK and candidates:
            rerank_started = perf_counter()
            rerank_count = min(self._settings.rerank_top_k, len(candidates))
            before = candidates[:rerank_count]
            try:
                scores = self._reranker.score(
                    query, [build_dense_document(item.product) for item in before]
                )
                if len(scores) != rerank_count:
                    raise ProviderError("reranker returned the wrong score count")
                scored = [
                    replace(candidate, rerank_score=score)
                    for candidate, score in zip(before, scores, strict=True)
                ]
                scored.sort(
                    key=lambda item: (
                        -(item.rerank_score or 0.0),
                        -(item.rrf_score or 0.0),
                        item.product.title.casefold(),
                        str(item.product.id),
                    )
                )
                candidates = [*scored, *candidates[rerank_count:]]
                actual_mode = "hybrid_rerank"
                trace["rerank"] = _rerank_trace(before, scored)
            except ProviderCircuitOpenError:
                trace["degraded_reason"] = "reranker_circuit_open"
                actual_mode = "hybrid_rrf_fallback"
            except ProviderTimeoutError:
                trace["degraded_reason"] = "reranker_timeout"
                actual_mode = "hybrid_rrf_fallback"
            except (ProviderError, ValueError):
                trace["degraded_reason"] = "reranker_error"
                actual_mode = "hybrid_rrf_fallback"
            trace["latency_ms"]["rerank"] = _elapsed_ms(rerank_started)

        trace["latency_ms"]["total"] = _elapsed_ms(started)
        return SearchExecution(actual_mode, candidates, len(candidates), trace)


def reciprocal_rank_fusion(
    lexical_hits: list[SearchHit],
    dense_hits: list[DenseSearchHit],
    *,
    rrf_k: int,
    limit: int,
) -> list[RankedCandidate]:
    """Fuse incomparable channel scores using only stable rank positions."""

    candidates: dict[object, RankedCandidate] = {}
    for rank, lexical_hit in enumerate(lexical_hits, start=1):
        candidates[lexical_hit.product.id] = RankedCandidate(
            lexical_hit.product,
            lexical_hit.document_version,
            lexical_rank=rank,
            lexical_score=lexical_hit.lexical_score,
            rrf_score=1.0 / (rrf_k + rank),
        )
    for rank, dense_hit in enumerate(dense_hits, start=1):
        current = candidates.get(dense_hit.product.id)
        contribution = 1.0 / (rrf_k + rank)
        if current is None:
            candidates[dense_hit.product.id] = RankedCandidate(
                dense_hit.product,
                dense_hit.document_version,
                dense_rank=rank,
                dense_score=dense_hit.dense_score,
                rrf_score=contribution,
            )
        else:
            candidates[dense_hit.product.id] = replace(
                current,
                dense_rank=rank,
                dense_score=dense_hit.dense_score,
                rrf_score=(current.rrf_score or 0.0) + contribution,
            )
    ranked = sorted(
        candidates.values(),
        key=lambda item: (
            -(item.rrf_score or 0.0),
            item.product.title.casefold(),
            str(item.product.id),
        ),
    )
    return ranked[:limit]


def _lexical_trace(hits: list[SearchHit]) -> list[dict[str, object]]:
    return [
        {"rank": rank, "source_id": hit.product.source_id, "score": hit.lexical_score}
        for rank, hit in enumerate(hits, start=1)
    ]


def _dense_trace(hits: list[DenseSearchHit]) -> list[dict[str, object]]:
    return [
        {"rank": rank, "source_id": hit.product.source_id, "score": hit.dense_score}
        for rank, hit in enumerate(hits, start=1)
    ]


def _fusion_trace(items: list[RankedCandidate]) -> list[dict[str, object]]:
    return [
        {
            "rank": rank,
            "source_id": item.product.source_id,
            "lexical_rank": item.lexical_rank,
            "dense_rank": item.dense_rank,
            "rrf_score": item.rrf_score,
        }
        for rank, item in enumerate(items, start=1)
    ]


def _rerank_trace(
    before: list[RankedCandidate], after: list[RankedCandidate]
) -> list[dict[str, object]]:
    previous = {item.product.id: rank for rank, item in enumerate(before, start=1)}
    return [
        {
            "source_id": item.product.source_id,
            "rank_before": previous[item.product.id],
            "rank_after": rank,
            "rerank_score": item.rerank_score,
        }
        for rank, item in enumerate(after, start=1)
    ]


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)
