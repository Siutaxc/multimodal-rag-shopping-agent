"""HTTP contract for opaque asset IDs, hard filters, and multimodal scores."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from app.api.multimodal import get_multimodal_search_service
from app.core.settings import Settings
from app.db.models import Product
from app.db.products import ProductFilters
from app.domain.products import ProductCategory
from app.images.search import MultimodalCandidate, MultimodalSearchExecution
from app.main import create_app
from fastapi.testclient import TestClient


class FakeMultimodalService:
    def __init__(self, product: Product) -> None:
        self.product = product
        self.asset_id: UUID | None = None
        self.query: str | None = None
        self.filters: ProductFilters | None = None

    def search(
        self, *, asset_id: UUID, query: str | None, filters: ProductFilters
    ) -> MultimodalSearchExecution:
        self.asset_id = asset_id
        self.query = query
        self.filters = filters
        return MultimodalSearchExecution(
            "multimodal_rrf",
            [
                MultimodalCandidate(
                    product=self.product,
                    text_rank=2,
                    image_rank=1,
                    image_score=0.82,
                    matched_image_id=uuid4(),
                    fusion_score=0.035,
                )
            ],
            1,
            {
                "parameters": {"rrf_k": 60},
                "models": {"image_embedding": "siglip2@fixture:768"},
                "degraded_reason": None,
                "channels": {"image": [{"rank": 1}]},
                "fusion": [{"rank": 1}],
                "latency_ms": {"total": 1.0},
            },
        )


@pytest.fixture
def client_and_service() -> Iterator[tuple[TestClient, FakeMultimodalService]]:
    now = datetime(2026, 7, 22, tzinfo=UTC)
    product = Product(
        id=uuid4(),
        source_name="fixture",
        source_id="fixture-001",
        source_version="v1",
        transformation_version="stage2-v1",
        idempotency_key="a" * 64,
        dedupe_key="b" * 64,
        title="Auralis Metro ANC 40",
        brand="Auralis",
        category=ProductCategory.OVER_EAR,
        description="通勤耳机",
        price_amount=Decimal("899"),
        currency="CNY",
        price_observed_at=now,
        wireless=True,
        anc=True,
        battery_hours=Decimal("40"),
        weight_grams=Decimal("245"),
        colors=["黑色"],
        codecs=["AAC"],
        water_resistance=None,
        microphone="双麦克风",
        source_url="https://fixtures.shoplens.local/products/fixture-001",
        images=[],
        documents=[],
        review_evidence=[],
        created_at=now,
        updated_at=now,
    )
    service = FakeMultimodalService(product)
    application = create_app(Settings(app_env="test", _env_file=None))
    application.dependency_overrides[get_multimodal_search_service] = lambda: service
    with TestClient(application) as client:
        yield client, service


def test_multimodal_search_keeps_asset_query_filters_and_channel_scores(
    client_and_service: tuple[TestClient, FakeMultimodalService],
) -> None:
    client, service = client_and_service
    asset_id = uuid4()
    response = client.post(
        "/api/v1/multimodal-search",
        json={
            "asset_id": str(asset_id),
            "query": "  通勤降噪  ",
            "filters": {
                "category": "over_ear",
                "price_max": "1000",
                "currency": "CNY",
                "anc": True,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_mode"] == "multimodal_rrf"
    assert body["items"][0]["image_score"] == 0.82
    assert body["items"][0]["fusion_score"] == 0.035
    assert service.asset_id == asset_id
    assert service.query == "通勤降噪"
    assert service.filters is not None
    assert service.filters.price_max == Decimal("1000")
    assert service.filters.anc is True


def test_multimodal_search_rejects_unknown_fields(
    client_and_service: tuple[TestClient, FakeMultimodalService],
) -> None:
    client, service = client_and_service
    response = client.post(
        "/api/v1/multimodal-search",
        json={"asset_id": str(uuid4()), "filters": {"sql": "drop table products"}},
    )

    assert response.status_code == 422
    assert service.asset_id is None
