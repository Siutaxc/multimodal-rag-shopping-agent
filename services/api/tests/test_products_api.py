"""HTTP contract tests for product pages and structured filter parsing."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast
from uuid import UUID, uuid4

import pytest
from app.api.products import get_product_repository
from app.core.settings import Settings
from app.db.models import Product
from app.db.products import ProductFilters
from app.domain.products import ProductCategory
from app.main import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeProductRepository:
    """Capture route filters without opening a database connection."""

    def __init__(self, product: Product) -> None:
        self.product = product
        self.last_filters: ProductFilters | None = None

    def list_products(self, filters: ProductFilters) -> tuple[list[Product], int]:
        self.last_filters = filters
        return [self.product], 1

    def get_product(self, product_id: UUID) -> Product | None:
        return self.product if product_id == self.product.id else None


@pytest.fixture
def product() -> Product:
    now = datetime(2026, 7, 20, tzinfo=UTC)
    return Product(
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


@pytest.fixture
def client_and_repository(
    product: Product,
) -> Iterator[tuple[TestClient, FakeProductRepository]]:
    application = create_app(Settings(app_env="test", _env_file=None))
    repository = FakeProductRepository(product)
    application.dependency_overrides[get_product_repository] = lambda: repository
    with TestClient(application) as client:
        yield client, repository


def test_list_parses_whitelisted_hard_filters(
    client_and_repository: tuple[TestClient, FakeProductRepository],
) -> None:
    client, repository = client_and_repository
    response = client.get(
        "/api/v1/products",
        params={
            "category": "in_ear",
            "price_max": "500.00",
            "currency": "CNY",
            "anc": "true",
            "battery_hours_min": "7.5",
            "color": "黑色",
            "codec": "aac",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    filters = repository.last_filters
    assert filters is not None
    assert filters.category == ProductCategory.IN_EAR
    assert filters.price_max == Decimal("500.00")
    assert filters.anc is True
    assert filters.battery_hours_min == Decimal("7.5")


def test_list_rejects_inverted_price_range_before_querying_repository(
    client_and_repository: tuple[TestClient, FakeProductRepository],
) -> None:
    client, repository = client_and_repository
    response = client.get("/api/v1/products?price_min=500&price_max=100")

    assert response.status_code == 422
    assert response.json()["detail"] == "price_min must not exceed price_max"
    assert repository.last_filters is None


def test_detail_contains_source_and_price_timestamp(
    client_and_repository: tuple[TestClient, FakeProductRepository], product: Product
) -> None:
    client, _ = client_and_repository
    response = client.get(f"/api/v1/products/{product.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["source_id"] == "fixture-003"
    assert body["source_url"].startswith("https://")
    assert body["price_observed_at"] == "2026-07-20T00:00:00Z"


def test_unknown_product_returns_404(
    client_and_repository: tuple[TestClient, FakeProductRepository],
) -> None:
    client, _ = client_and_repository
    response = client.get(f"/api/v1/products/{uuid4()}")
    assert response.status_code == 404


def test_repository_override_is_installed_on_fastapi_app(
    client_and_repository: tuple[TestClient, FakeProductRepository],
) -> None:
    client, _ = client_and_repository
    assert get_product_repository in cast(FastAPI, client.app).dependency_overrides
