"""Reusable synthetic products and finite fake tools for stage-six unit tests."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.agent.tools import CatalogCandidate, CatalogToolResult
from app.db.models import Product, ReviewEvidence
from app.db.products import ProductFilters
from app.domain.products import ProductCategory, ReviewTopic


def make_product(
    index: int = 1,
    *,
    price: Decimal = Decimal("899.00"),
    description: str = "Synthetic product facts",
    include_review: bool = True,
) -> Product:
    now = datetime(2026, 7, 22, tzinfo=UTC)
    product = Product(
        id=uuid4(),
        source_name="fixture",
        source_id=f"fixture-agent-{index:03d}",
        source_version="v1",
        transformation_version="stage2-v1",
        idempotency_key=f"{index:064x}"[-64:],
        dedupe_key=f"{index + 1000:064x}"[-64:],
        title=f"Auralis Agent {index}",
        brand="Auralis",
        category=ProductCategory.OVER_EAR,
        description=description,
        price_amount=price,
        currency="CNY",
        price_observed_at=now,
        wireless=True,
        anc=True,
        battery_hours=Decimal("40.00"),
        weight_grams=Decimal("245.00"),
        colors=["黑色"],
        codecs=["AAC", "LDAC"],
        water_resistance=None,
        microphone="双麦克风",
        source_url=f"https://fixtures.shoplens.local/products/agent-{index}",
        images=[],
        documents=[],
        review_evidence=[],
        created_at=now,
        updated_at=now,
    )
    if include_review:
        product.review_evidence.append(
            ReviewEvidence(
                id=uuid4(),
                product_id=product.id,
                source_name="fixture",
                source_review_id=f"review-{index}",
                topic=ReviewTopic.COMFORT,
                excerpt="戴眼镜连续使用时压力可接受。",
                rating=Decimal("4.0"),
                reviewed_at=now,
                source_url=f"https://fixtures.shoplens.local/reviews/{index}",
                created_at=now,
                updated_at=now,
            )
        )
    return product


class FakeAgentTools:
    def __init__(self, products: list[Product]) -> None:
        self.products = products
        self.search_filters: list[ProductFilters] = []
        self.calls: list[str] = []

    def search_catalog(
        self,
        query: str,
        filters: ProductFilters,
        *,
        asset_id: UUID | None,
    ) -> CatalogToolResult:
        del query, asset_id
        self.calls.append("search_catalog")
        self.search_filters.append(filters)
        candidates = [product for product in self.products if _matches(product, filters)]
        return CatalogToolResult(
            mode="hybrid_rerank",
            candidates=[CatalogCandidate(product, {"rerank_score": 0.9}) for product in candidates],
            total=len(candidates),
            trace={"degraded_reason": None, "latency_ms": {"total": 1.0}},
        )

    def get_product_detail(self, product_ids: list[UUID]) -> list[Product]:
        self.calls.append("get_product_detail")
        return _ordered(self.products, product_ids)

    def compare_products(self, product_ids: list[UUID]) -> list[Product]:
        self.calls.append("compare_products")
        return _ordered(self.products, product_ids)


def _ordered(products: list[Product], product_ids: list[UUID]) -> list[Product]:
    index = {product.id: product for product in products}
    return [index[product_id] for product_id in product_ids if product_id in index]


def _matches(product: Product, filters: ProductFilters) -> bool:
    if filters.price_max is not None and product.price_amount > filters.price_max:
        return False
    if filters.price_min is not None and product.price_amount < filters.price_min:
        return False
    if filters.anc is not None and product.anc is not filters.anc:
        return False
    return not (filters.category is not None and product.category != filters.category)
