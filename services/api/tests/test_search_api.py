"""HTTP contract tests for hybrid search, trace, and hard-filter validation."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast
from uuid import uuid4

import pytest
from app.api.search import get_search_cache, get_search_service
from app.core.cache import MemoryResponseCache
from app.core.settings import Settings
from app.db.models import Product
from app.db.products import ProductFilters
from app.domain.products import ProductCategory
from app.main import create_app
from app.retrieval.hybrid import RankedCandidate, SearchExecution, SearchMode
from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeSearchService:
    """Capture requests without opening PostgreSQL in an HTTP unit test."""

    def __init__(self, product: Product) -> None:
        self.product = product
        self.last_query: str | None = None
        self.last_filters: ProductFilters | None = None
        self.last_mode: SearchMode | None = None
        self.call_count = 0

    def search(
        self, query_text: str, filters: ProductFilters, *, mode: SearchMode
    ) -> SearchExecution:
        self.last_query = query_text
        self.call_count += 1
        self.last_filters = filters
        self.last_mode = mode
        return SearchExecution(
            "hybrid_rerank",
            [
                RankedCandidate(
                    self.product,
                    "stage4-dense-v1",
                    lexical_rank=1,
                    lexical_score=1.125,
                    dense_rank=2,
                    dense_score=0.8,
                    rrf_score=0.03,
                    rerank_score=0.9,
                )
            ],
            1,
            {
                "parameters": {"rrf_k": 60},
                "models": {"embedding": "fixture"},
                "degraded_reason": None,
                "channels": {},
                "fusion": [],
                "rerank": [],
                "latency_ms": {"total": 1.0},
            },
        )


@pytest.fixture
def client_and_repository() -> Iterator[tuple[TestClient, FakeSearchService]]:
    now = datetime(2026, 7, 20, tzinfo=UTC)
    product = Product(
        id=uuid4(),
        source_name="fixture",
        source_id="fixture-003",
        source_version="v1",
        transformation_version="stage2-v1",
        idempotency_key="a" * 64,
        dedupe_key="b" * 64,
        title="MetroTone Buds N8",
        brand="MetroTone",
        category=ProductCategory.IN_EAR,
        description="Synthetic product",
        price_amount=Decimal("499.00"),
        currency="CNY",
        price_observed_at=now,
        wireless=True,
        anc=True,
        battery_hours=Decimal("8.00"),
        weight_grams=Decimal("5.20"),
        colors=["黑色"],
        codecs=["AAC"],
        water_resistance="IP54",
        microphone="双麦克风",
        source_url="https://fixtures.shoplens.local/products/fixture-003",
        images=[],
        documents=[],
        review_evidence=[],
        created_at=now,
        updated_at=now,
    )
    repository = FakeSearchService(product)
    application = create_app(Settings(app_env="test", _env_file=None))
    application.dependency_overrides[get_search_service] = lambda: repository
    with TestClient(application) as client:
        yield client, repository


def test_search_returns_ranked_product_and_applies_hard_filters(
    client_and_repository: tuple[TestClient, FakeSearchService],
) -> None:
    client, repository = client_and_repository
    response = client.post(
        "/api/v1/search",
        json={
            "query": "  MetroTone N8  ",
            "mode": "rerank",
            "page_size": 5,
            "filters": {
                "category": "in_ear",
                "price_max": "500.00",
                "currency": "cny",
                "anc": True,
                "codec": "aac",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_mode"] == "hybrid_rerank"
    assert body["items"][0]["rank"] == 1
    assert body["items"][0]["lexical_score"] == 1.125
    assert body["items"][0]["dense_score"] == 0.8
    assert body["items"][0]["rerank_score"] == 0.9
    assert body["trace"]["models"]["embedding"] == "fixture"
    assert body["items"][0]["product"]["source_name"] == "fixture"
    assert repository.last_query == "MetroTone N8"
    assert repository.last_filters is not None
    assert repository.last_filters.price_max == Decimal("500.00")
    assert repository.last_filters.anc is True
    assert repository.last_mode == SearchMode.RERANK


@pytest.mark.parametrize(
    "payload",
    [
        {"query": "   "},
        {"query": "headphones", "filters": {"price_min": 500, "price_max": 100}},
        {"query": "headphones", "filters": {"unreviewed_sql": "drop table products"}},
    ],
)
def test_search_rejects_blank_inverted_or_unknown_input(
    client_and_repository: tuple[TestClient, FakeSearchService], payload: dict[str, object]
) -> None:
    client, repository = client_and_repository
    response = client.post("/api/v1/search", json=payload)

    assert response.status_code == 422
    assert repository.last_query is None


def test_search_cache_hit_skips_duplicate_retrieval(
    client_and_repository: tuple[TestClient, FakeSearchService],
) -> None:
    client, repository = client_and_repository
    cache = MemoryResponseCache()
    cast(FastAPI, client.app).dependency_overrides[get_search_cache] = lambda: cache

    first = client.post("/api/v1/search", json={"query": "MetroTone N8"})
    second = client.post("/api/v1/search", json={"query": "MetroTone N8"})

    assert first.headers["X-ShopLens-Cache"] == "MISS"
    assert second.headers["X-ShopLens-Cache"] == "HIT"
    assert repository.call_count == 1
