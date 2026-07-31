"""Reviewed shopping tools; none accept SQL, URLs, files, code, or arbitrary actions."""

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.db.models import Product
from app.db.products import ProductFilters, ProductRepository
from app.images.search import MultimodalSearchService
from app.retrieval.hybrid import HybridSearchService, SearchMode


@dataclass(frozen=True)
class CatalogCandidate:
    product: Product
    scores: dict[str, float | int | str | None]


@dataclass(frozen=True)
class CatalogToolResult:
    mode: str
    candidates: list[CatalogCandidate]
    total: int
    trace: dict[str, Any]


class AgentToolbox(Protocol):
    def search_catalog(
        self,
        query: str,
        filters: ProductFilters,
        *,
        asset_id: UUID | None,
    ) -> CatalogToolResult: ...

    def get_product_detail(self, product_ids: list[UUID]) -> list[Product]: ...

    def compare_products(self, product_ids: list[UUID]) -> list[Product]: ...


class ShoppingAgentTools:
    """Thin adapters around frozen stage 3-5 deterministic retrieval contracts."""

    def __init__(
        self,
        products: ProductRepository,
        text_search: HybridSearchService,
        multimodal_search: MultimodalSearchService,
    ) -> None:
        self._products = products
        self._text_search = text_search
        self._multimodal_search = multimodal_search

    def search_catalog(
        self,
        query: str,
        filters: ProductFilters,
        *,
        asset_id: UUID | None,
    ) -> CatalogToolResult:
        if asset_id is not None:
            execution = self._multimodal_search.search(
                asset_id=asset_id,
                query=query,
                filters=filters,
            )
            return CatalogToolResult(
                mode=execution.mode,
                candidates=[
                    CatalogCandidate(
                        candidate.product,
                        {
                            "text_rank": candidate.text_rank,
                            "image_rank": candidate.image_rank,
                            "image_score": candidate.image_score,
                            "fusion_score": candidate.fusion_score,
                        },
                    )
                    for candidate in execution.items
                ],
                total=execution.total,
                trace=execution.trace,
            )
        text_execution = self._text_search.search(query, filters, mode=SearchMode.RERANK)
        return CatalogToolResult(
            mode=text_execution.mode,
            candidates=[
                CatalogCandidate(
                    candidate.product,
                    {
                        "lexical_rank": candidate.lexical_rank,
                        "dense_rank": candidate.dense_rank,
                        "rrf_score": candidate.rrf_score,
                        "rerank_score": candidate.rerank_score,
                    },
                )
                for candidate in text_execution.items
            ],
            total=text_execution.total,
            trace=text_execution.trace,
        )

    def get_product_detail(self, product_ids: list[UUID]) -> list[Product]:
        return self._products.get_products(product_ids)

    def compare_products(self, product_ids: list[UUID]) -> list[Product]:
        if not 2 <= len(product_ids) <= 4:
            raise ValueError("compare_products requires two to four product IDs")
        return self._products.get_products(product_ids)
