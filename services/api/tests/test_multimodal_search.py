"""Rank-only multimodal fusion and image-provider degradation tests."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.core.settings import Settings
from app.db.images import ImageSearchHit
from app.db.models import Product, UploadedImageAsset
from app.db.products import ProductFilters
from app.domain.products import ProductCategory
from app.images.search import MultimodalSearchService, multimodal_rank_fusion
from app.providers.retrieval import ProviderIdentity, ProviderTimeoutError
from app.providers.storage import LocalObjectStorage
from app.retrieval.hybrid import RankedCandidate, SearchExecution

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def _product(source_id: str) -> Product:
    now = datetime(2026, 7, 22, tzinfo=UTC)
    return Product(
        id=uuid4(),
        source_name="fixture",
        source_id=source_id,
        source_version="v1",
        transformation_version="stage2-v1",
        idempotency_key=source_id.ljust(64, "a")[:64],
        dedupe_key=source_id.ljust(64, "b")[:64],
        title=source_id,
        brand="Test",
        category=ProductCategory.OVER_EAR,
        description="test",
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
        microphone=None,
        source_url=f"https://fixtures.shoplens.local/{source_id}",
        images=[],
        documents=[],
        review_evidence=[],
        created_at=now,
        updated_at=now,
    )


def test_multimodal_rrf_rewards_cross_channel_presence_without_adding_raw_scores() -> None:
    text_only = _product("text-only")
    shared = _product("shared")
    image_only = _product("image-only")
    image_id = uuid4()

    fused = multimodal_rank_fusion(
        [RankedCandidate(text_only, "v", rerank_score=0.99), RankedCandidate(shared, "v")],
        [
            ImageSearchHit(shared, image_id, 0.2, "image-v1"),
            ImageSearchHit(image_only, uuid4(), 0.99, "image-v1"),
        ],
        rrf_k=60,
        text_weight=1.0,
        image_weight=1.25,
        limit=3,
    )

    assert [item.product.source_id for item in fused] == ["shared", "image-only", "text-only"]
    assert fused[0].image_score == 0.2
    assert fused[0].fusion_score is not None
    assert fused[0].fusion_score != fused[0].image_score


class _Assets:
    def __init__(self, asset: UploadedImageAsset) -> None:
        self.asset = asset

    def get(self, asset_id: object) -> UploadedImageAsset | None:
        return self.asset if asset_id == self.asset.id else None


class _Images:
    def search(self, *_args: object, **_kwargs: object) -> tuple[list[ImageSearchHit], int]:
        raise AssertionError("repository must not run after provider timeout")


class _TextSearch:
    def __init__(self, product: Product) -> None:
        self.product = product

    def search(self, *_args: object, **_kwargs: object) -> SearchExecution:
        return SearchExecution(
            "hybrid_rerank",
            [RankedCandidate(self.product, "stage4", rerank_score=0.8)],
            1,
            {"degraded_reason": None},
        )


class _TimeoutImages:
    identity = ProviderIdentity("siglip2", "timeout-v1", 768)

    def embed_images(self, images: Sequence[bytes]) -> list[list[float]]:
        raise ProviderTimeoutError("timeout")


def test_image_timeout_degrades_mixed_query_to_text_but_not_pure_image() -> None:
    storage = LocalObjectStorage(WORKSPACE_ROOT / "data" / "fixtures")
    image_path = WORKSPACE_ROOT / "data" / "fixtures" / "images" / "fixture-001.png"
    now = datetime(2026, 7, 22, tzinfo=UTC)
    asset = UploadedImageAsset(
        id=uuid4(),
        storage_key="images/fixture-001.png",
        original_sha256="a" * 64,
        content_sha256="b" * 64,
        media_type="image/png",
        byte_size=image_path.stat().st_size,
        width=10,
        height=10,
        created_at=now,
        updated_at=now,
    )
    product = _product("text-fallback")
    service = MultimodalSearchService(
        _Assets(asset),
        _Images(),
        _TextSearch(product),  # type: ignore[arg-type]
        _TimeoutImages(),
        storage,
        Settings(app_env="test", _env_file=None),
    )

    mixed = service.search(asset_id=asset.id, query="通勤降噪", filters=ProductFilters())
    pure = service.search(asset_id=asset.id, query=None, filters=ProductFilters())

    assert mixed.mode == "multimodal_text_fallback"
    assert mixed.items[0].product is product
    assert mixed.trace["degraded_reason"] == "image_embedding_timeout"
    assert pure.mode == "image_unavailable"
    assert pure.items == []
