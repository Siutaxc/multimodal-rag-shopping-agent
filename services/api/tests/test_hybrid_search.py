"""RRF stability and reranker fallback tests."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.core.settings import Settings
from app.db.models import Product
from app.db.products import ProductFilters
from app.db.search import DenseSearchHit, SearchHit
from app.domain.products import ProductCategory
from app.providers.retrieval import ProviderIdentity, ProviderTimeoutError
from app.retrieval.hybrid import HybridSearchService, SearchMode, reciprocal_rank_fusion


def _product(source_id: str, title: str) -> Product:
    now = datetime(2026, 7, 22, tzinfo=UTC)
    return Product(
        id=uuid4(),
        source_name="fixture",
        source_id=source_id,
        source_version="v1",
        transformation_version="stage2-v1",
        idempotency_key=source_id.ljust(64, "a")[:64],
        dedupe_key=source_id.ljust(64, "b")[:64],
        title=title,
        brand="Test",
        category=ProductCategory.OVER_EAR,
        description="通勤主动降噪",
        price_amount=Decimal("500"),
        currency="CNY",
        price_observed_at=now,
        wireless=True,
        anc=True,
        battery_hours=Decimal("40"),
        weight_grams=Decimal("200"),
        colors=["黑色"],
        codecs=["AAC"],
        water_resistance=None,
        microphone="麦克风",
        source_url=f"https://fixtures.shoplens.local/{source_id}",
        images=[],
        documents=[],
        review_evidence=[],
        created_at=now,
        updated_at=now,
    )


def test_rrf_rewards_candidates_present_in_both_channels() -> None:
    first = _product("fixture-a", "A")
    second = _product("fixture-b", "B")
    third = _product("fixture-c", "C")

    fused = reciprocal_rank_fusion(
        [SearchHit(first, 10.0, "lex"), SearchHit(second, 9.0, "lex")],
        [DenseSearchHit(second, 0.9, "dense"), DenseSearchHit(third, 0.8, "dense")],
        rrf_k=60,
        limit=3,
    )

    assert [item.product.source_id for item in fused] == ["fixture-b", "fixture-a", "fixture-c"]
    assert fused[0].lexical_rank == 2
    assert fused[0].dense_rank == 1


class _LexicalRepository:
    def __init__(self, product: Product) -> None:
        self.product = product

    def search(self, query_text: str, filters: ProductFilters) -> tuple[list[SearchHit], int]:
        return [SearchHit(self.product, 1.0, "stage3-lexical-v1")], 1


class _DenseRepository:
    def __init__(self, product: Product) -> None:
        self.product = product

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
    ) -> tuple[list[DenseSearchHit], int]:
        return [DenseSearchHit(self.product, 0.8, document_version)], 1


class _EmbeddingProvider:
    identity = ProviderIdentity("BAAI/bge-m3", "test-v1", 1024)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.0] * 1024 for _ in texts]


class _TimeoutReranker:
    identity = ProviderIdentity("BAAI/bge-reranker-v2-m3", "test-v1")

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        raise ProviderTimeoutError("timeout")


def test_reranker_timeout_falls_back_to_unchanged_rrf_order() -> None:
    product = _product("fixture-a", "A")
    settings = Settings(app_env="test", _env_file=None)
    service = HybridSearchService(
        _LexicalRepository(product),
        _DenseRepository(product),
        _EmbeddingProvider(),
        _TimeoutReranker(),
        settings,
    )

    result = service.search("通勤降噪", ProductFilters(), mode=SearchMode.RERANK)

    assert result.mode == "hybrid_rrf_fallback"
    assert result.trace["degraded_reason"] == "reranker_timeout"
    assert result.items[0].product is product
    assert result.items[0].rerank_score is None
