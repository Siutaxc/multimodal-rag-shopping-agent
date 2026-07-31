"""Pure-image and rank-fused text/image retrieval with explicit degradation."""

from dataclasses import dataclass, replace
from time import perf_counter
from typing import Any, Protocol
from uuid import UUID

from app.core.settings import Settings
from app.db.images import ImageSearchHit
from app.db.models import Product, UploadedImageAsset
from app.db.products import ProductFilters
from app.images.indexing import IMAGE_REPRESENTATION_VERSION
from app.providers.images import ImageEmbeddingProvider
from app.providers.retrieval import (
    ProviderCircuitOpenError,
    ProviderError,
    ProviderTimeoutError,
)
from app.providers.storage import ObjectStorage
from app.retrieval.hybrid import HybridSearchService, RankedCandidate, SearchMode


class AssetRepository(Protocol):
    def get(self, asset_id: UUID) -> UploadedImageAsset | None: ...


class ImageRepository(Protocol):
    def search(
        self,
        query_vector: list[float],
        filters: ProductFilters,
        *,
        model_name: str,
        model_version: str,
        dimension: int,
        representation_version: str,
        limit: int,
    ) -> tuple[list[ImageSearchHit], int]: ...


class AssetNotFoundError(LookupError):
    """The opaque upload ID does not resolve in the current database."""


@dataclass(frozen=True)
class MultimodalCandidate:
    product: Product
    lexical_rank: int | None = None
    lexical_score: float | None = None
    dense_rank: int | None = None
    dense_score: float | None = None
    text_rank: int | None = None
    text_rrf_score: float | None = None
    rerank_score: float | None = None
    image_rank: int | None = None
    image_score: float | None = None
    matched_image_id: UUID | None = None
    fusion_score: float | None = None


@dataclass(frozen=True)
class MultimodalSearchExecution:
    mode: str
    items: list[MultimodalCandidate]
    total: int
    trace: dict[str, Any]


class MultimodalSearchService:
    """Keep image scores independent and fuse only stable channel ranks."""

    def __init__(
        self,
        assets: AssetRepository,
        images: ImageRepository,
        text_search: HybridSearchService,
        image_provider: ImageEmbeddingProvider,
        storage: ObjectStorage,
        settings: Settings,
    ) -> None:
        self._assets = assets
        self._images = images
        self._text_search = text_search
        self._image_provider = image_provider
        self._storage = storage
        self._settings = settings

    def search(
        self, *, asset_id: UUID, query: str | None, filters: ProductFilters
    ) -> MultimodalSearchExecution:
        started = perf_counter()
        asset = self._assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(str(asset_id))
        normalized_query = query.strip() if query is not None else None
        if normalized_query == "":
            normalized_query = None

        text_execution = (
            self._text_search.search(normalized_query, filters, mode=SearchMode.RERANK)
            if normalized_query is not None
            else None
        )
        trace: dict[str, Any] = {
            "parameters": {
                "image_candidate_k": self._settings.image_candidate_k,
                "fusion_candidate_k": self._settings.fusion_candidate_k,
                "rrf_k": self._settings.rrf_k,
                "text_weight": self._settings.multimodal_text_weight,
                "image_weight": self._settings.multimodal_image_weight,
            },
            "models": {
                "image_embedding": self._image_provider.identity.version_key,
                "image_representation": IMAGE_REPRESENTATION_VERSION,
            },
            "asset": {
                "asset_id": str(asset.id),
                "content_sha256": asset.content_sha256,
                "width": asset.width,
                "height": asset.height,
            },
            "degraded_reason": None,
            "channels": {"image": []},
            "text_trace": text_execution.trace if text_execution is not None else None,
            "fusion": [],
            "latency_ms": {},
        }
        if text_execution is not None and text_execution.trace.get("degraded_reason"):
            trace["degraded_reason"] = f"text_{text_execution.trace['degraded_reason']}"

        try:
            image_started = perf_counter()
            content = self._storage.resolve(asset.storage_key).read_bytes()
            vectors = self._image_provider.embed_images([content])
            if len(vectors) != 1:
                raise ProviderError("image provider returned the wrong batch size")
            identity = self._image_provider.identity
            assert identity.dimension is not None
            image_hits, image_total = self._images.search(
                vectors[0],
                filters,
                model_name=identity.model_name,
                model_version=identity.model_version,
                dimension=identity.dimension,
                representation_version=IMAGE_REPRESENTATION_VERSION,
                limit=self._settings.image_candidate_k,
            )
            trace["latency_ms"]["image"] = _elapsed_ms(image_started)
            trace["channels"]["image"] = _image_trace(image_hits)
        except ProviderCircuitOpenError:
            return self._fallback(text_execution, trace, started, "image_embedding_circuit_open")
        except ProviderTimeoutError:
            return self._fallback(text_execution, trace, started, "image_embedding_timeout")
        except (OSError, ProviderError, ValueError):
            return self._fallback(text_execution, trace, started, "image_embedding_error")

        if not image_hits and image_total == 0:
            return self._fallback(text_execution, trace, started, "image_index_empty")
        if text_execution is None:
            candidates = [
                MultimodalCandidate(
                    product=hit.product,
                    image_rank=rank,
                    image_score=hit.image_score,
                    matched_image_id=hit.image_id,
                )
                for rank, hit in enumerate(image_hits, start=1)
            ]
            trace["latency_ms"]["total"] = _elapsed_ms(started)
            return MultimodalSearchExecution("pgvector_image", candidates, image_total, trace)

        fusion_started = perf_counter()
        candidates = multimodal_rank_fusion(
            text_execution.items,
            image_hits,
            rrf_k=self._settings.rrf_k,
            text_weight=self._settings.multimodal_text_weight,
            image_weight=self._settings.multimodal_image_weight,
            limit=self._settings.fusion_candidate_k,
        )
        trace["latency_ms"]["fusion"] = _elapsed_ms(fusion_started)
        trace["fusion"] = _fusion_trace(candidates)
        trace["latency_ms"]["total"] = _elapsed_ms(started)
        return MultimodalSearchExecution("multimodal_rrf", candidates, len(candidates), trace)

    def _fallback(
        self,
        text_execution: Any,
        trace: dict[str, Any],
        started: float,
        reason: str,
    ) -> MultimodalSearchExecution:
        trace["degraded_reason"] = reason
        trace["latency_ms"]["total"] = _elapsed_ms(started)
        if text_execution is None:
            return MultimodalSearchExecution("image_unavailable", [], 0, trace)
        candidates = [
            _from_text(item, text_rank=rank)
            for rank, item in enumerate(text_execution.items, start=1)
        ]
        return MultimodalSearchExecution(
            "multimodal_text_fallback", candidates, text_execution.total, trace
        )


def multimodal_rank_fusion(
    text_items: list[RankedCandidate],
    image_hits: list[ImageSearchHit],
    *,
    rrf_k: int,
    text_weight: float,
    image_weight: float,
    limit: int,
) -> list[MultimodalCandidate]:
    """Fuse ranks only; raw text and image similarities remain separately inspectable."""

    candidates: dict[object, MultimodalCandidate] = {}
    for rank, item in enumerate(text_items, start=1):
        candidate = _from_text(item, text_rank=rank)
        candidates[item.product.id] = replace(candidate, fusion_score=text_weight / (rrf_k + rank))
    for rank, hit in enumerate(image_hits, start=1):
        contribution = image_weight / (rrf_k + rank)
        current = candidates.get(hit.product.id)
        if current is None:
            candidates[hit.product.id] = MultimodalCandidate(
                product=hit.product,
                image_rank=rank,
                image_score=hit.image_score,
                matched_image_id=hit.image_id,
                fusion_score=contribution,
            )
        else:
            candidates[hit.product.id] = replace(
                current,
                image_rank=rank,
                image_score=hit.image_score,
                matched_image_id=hit.image_id,
                fusion_score=(current.fusion_score or 0.0) + contribution,
            )
    return sorted(
        candidates.values(),
        key=lambda item: (
            -(item.fusion_score or 0.0),
            item.product.title.casefold(),
            str(item.product.id),
        ),
    )[:limit]


def _from_text(item: RankedCandidate, *, text_rank: int) -> MultimodalCandidate:
    return MultimodalCandidate(
        product=item.product,
        lexical_rank=item.lexical_rank,
        lexical_score=item.lexical_score,
        dense_rank=item.dense_rank,
        dense_score=item.dense_score,
        text_rank=text_rank,
        text_rrf_score=item.rrf_score,
        rerank_score=item.rerank_score,
    )


def _image_trace(hits: list[ImageSearchHit]) -> list[dict[str, object]]:
    return [
        {
            "rank": rank,
            "source_id": hit.product.source_id,
            "image_id": str(hit.image_id),
            "score": hit.image_score,
        }
        for rank, hit in enumerate(hits, start=1)
    ]


def _fusion_trace(items: list[MultimodalCandidate]) -> list[dict[str, object]]:
    return [
        {
            "rank": rank,
            "source_id": item.product.source_id,
            "text_rank": item.text_rank,
            "image_rank": item.image_rank,
            "fusion_score": item.fusion_score,
        }
        for rank, item in enumerate(items, start=1)
    ]


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)
