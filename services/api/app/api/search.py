"""Stage-four text search endpoint with selectable ablation modes and trace."""

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.api.products import ProductSummary
from app.core.cache import ResponseCache, cache_key, create_response_cache
from app.core.metrics import metrics
from app.core.settings import Settings, get_settings
from app.db.products import ProductFilters
from app.db.search import DenseSearchRepository, LexicalSearchRepository
from app.db.session import get_db_session
from app.domain.products import ProductCategory
from app.providers.retrieval import create_embedding_provider, create_reranker_provider
from app.retrieval.documents import LEXICAL_DOCUMENT_VERSION
from app.retrieval.hybrid import HybridSearchService, RankedCandidate, SearchMode
from app.retrieval.text_documents import DENSE_DOCUMENT_VERSION

router = APIRouter(prefix="/search", tags=["search"])


class SearchFiltersInput(BaseModel):
    """Only structured facts that can be enforced before ranking."""

    model_config = ConfigDict(extra="forbid")

    category: ProductCategory | None = None
    brand: str | None = Field(default=None, min_length=1, max_length=160)
    price_min: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    price_max: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    wireless: bool | None = None
    anc: bool | None = None
    battery_hours_min: Decimal | None = Field(default=None, gt=0, max_digits=7, decimal_places=2)
    weight_grams_max: Decimal | None = Field(default=None, gt=0, max_digits=9, decimal_places=2)
    color: str | None = Field(default=None, min_length=1, max_length=80)
    codec: str | None = Field(default=None, min_length=1, max_length=80)
    water_resistance: str | None = Field(default=None, min_length=2, max_length=32)

    @field_validator("brand", "color", "codec", "water_resistance")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @model_validator(mode="after")
    def validate_price_range(self) -> "SearchFiltersInput":
        if (
            self.price_min is not None
            and self.price_max is not None
            and self.price_min > self.price_max
        ):
            raise ValueError("price_min must not exceed price_max")
        return self


class SearchRequest(BaseModel):
    """A text query, one explicit ablation mode, and reviewed hard constraints."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=300)
    mode: SearchMode = SearchMode.RERANK
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=100)
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)

    @field_validator("query")
    @classmethod
    def reject_blank_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must contain searchable text")
        return value


class SearchResultItem(BaseModel):
    """One product with inspectable scores from every channel that touched it."""

    rank: int
    lexical_rank: int | None = None
    lexical_score: float | None = None
    dense_rank: int | None = None
    dense_score: float | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None
    document_version: str
    product: ProductSummary


class SearchResponse(BaseModel):
    """Stable hybrid result envelope used by the UI and evaluator."""

    retrieval_mode: str
    search_document_version: str = LEXICAL_DOCUMENT_VERSION
    dense_document_version: str = DENSE_DOCUMENT_VERSION
    query: str
    applied_filters: SearchFiltersInput
    items: list[SearchResultItem]
    page: int
    page_size: int
    total: int
    trace: dict[str, Any]


def get_search_service(
    session: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HybridSearchService:
    return HybridSearchService(
        LexicalSearchRepository(session),
        DenseSearchRepository(session),
        create_embedding_provider(settings),
        create_reranker_provider(settings),
        settings,
    )


def get_search_cache(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResponseCache:
    return create_response_cache(settings)


def _item(hit: RankedCandidate, *, rank: int) -> SearchResultItem:
    return SearchResultItem(
        rank=rank,
        lexical_rank=hit.lexical_rank,
        lexical_score=hit.lexical_score,
        dense_rank=hit.dense_rank,
        dense_score=hit.dense_score,
        rrf_score=hit.rrf_score,
        rerank_score=hit.rerank_score,
        document_version=hit.document_version,
        product=ProductSummary.model_validate(hit.product),
    )


@router.post("", response_model=SearchResponse, summary="Search products with PostgreSQL FTS")
def search_products(
    request: SearchRequest,
    service: Annotated[HybridSearchService, Depends(get_search_service)],
    response: Response,
    cache: Annotated[ResponseCache, Depends(get_search_cache)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SearchResponse:
    key = cache_key("text-search", request, settings)
    cached = cache.get(key)
    if cached is not None:
        try:
            result = SearchResponse.model_validate_json(cached)
        except ValueError:
            cached = None
        else:
            response.headers["X-ShopLens-Cache"] = "HIT"
            metrics.counter(
                "shoplens_search_cache_total",
                labels={"outcome": "hit"},
                help_text="Text-search response cache outcomes",
            )
            return result
    response.headers["X-ShopLens-Cache"] = "MISS"
    metrics.counter(
        "shoplens_search_cache_total",
        labels={"outcome": "miss"},
        help_text="Text-search response cache outcomes",
    )
    filters = ProductFilters(
        page=request.page,
        page_size=request.page_size,
        category=request.filters.category,
        brand=request.filters.brand,
        price_min=request.filters.price_min,
        price_max=request.filters.price_max,
        currency=request.filters.currency,
        wireless=request.filters.wireless,
        anc=request.filters.anc,
        battery_hours_min=request.filters.battery_hours_min,
        weight_grams_max=request.filters.weight_grams_max,
        color=request.filters.color,
        codec=request.filters.codec,
        water_resistance=request.filters.water_resistance,
    )
    execution = service.search(request.query, filters, mode=request.mode)
    offset = (request.page - 1) * request.page_size
    page_items = execution.items[offset : offset + request.page_size]
    result = SearchResponse(
        retrieval_mode=execution.mode,
        query=request.query,
        applied_filters=request.filters,
        items=[_item(hit, rank=offset + index) for index, hit in enumerate(page_items, start=1)],
        page=request.page,
        page_size=request.page_size,
        total=execution.total,
        trace=execution.trace,
    )
    cache.set(key, result.model_dump_json())
    return result
