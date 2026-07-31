"""Pure-image and image-plus-text product search HTTP contract."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.api.products import ProductSummary
from app.api.search import SearchFiltersInput
from app.core.cache import ResponseCache, cache_key, create_response_cache
from app.core.metrics import metrics
from app.core.settings import Settings, get_settings
from app.db.images import ImageSearchRepository, UploadedImageAssetRepository
from app.db.products import ProductFilters
from app.db.search import DenseSearchRepository, LexicalSearchRepository
from app.db.session import get_db_session
from app.images.search import (
    AssetNotFoundError,
    MultimodalCandidate,
    MultimodalSearchService,
)
from app.providers.images import create_image_embedding_provider
from app.providers.retrieval import create_embedding_provider, create_reranker_provider
from app.providers.storage import LocalObjectStorage
from app.retrieval.hybrid import HybridSearchService

router = APIRouter(prefix="/multimodal-search", tags=["search"])


class MultimodalSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    query: str | None = Field(default=None, max_length=300)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=100)
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)

    @field_validator("query")
    @classmethod
    def normalize_optional_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class MultimodalSearchItem(BaseModel):
    rank: int
    lexical_rank: int | None
    lexical_score: float | None
    dense_rank: int | None
    dense_score: float | None
    text_rank: int | None
    text_rrf_score: float | None
    rerank_score: float | None
    image_rank: int | None
    image_score: float | None
    matched_image_id: UUID | None
    fusion_score: float | None
    product: ProductSummary


class MultimodalSearchResponse(BaseModel):
    retrieval_mode: str
    query: str | None
    asset_id: UUID
    applied_filters: SearchFiltersInput
    items: list[MultimodalSearchItem]
    page: int
    page_size: int
    total: int
    trace: dict[str, Any]


def get_multimodal_search_service(
    session: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MultimodalSearchService:
    text_service = HybridSearchService(
        LexicalSearchRepository(session),
        DenseSearchRepository(session),
        create_embedding_provider(settings),
        create_reranker_provider(settings),
        settings,
    )
    return MultimodalSearchService(
        UploadedImageAssetRepository(session),
        ImageSearchRepository(session),
        text_service,
        create_image_embedding_provider(settings),
        LocalObjectStorage(settings.object_storage_path),
        settings,
    )


def get_multimodal_cache(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResponseCache:
    return create_response_cache(settings)


def _item(candidate: MultimodalCandidate, rank: int) -> MultimodalSearchItem:
    return MultimodalSearchItem(
        rank=rank,
        lexical_rank=candidate.lexical_rank,
        lexical_score=candidate.lexical_score,
        dense_rank=candidate.dense_rank,
        dense_score=candidate.dense_score,
        text_rank=candidate.text_rank,
        text_rrf_score=candidate.text_rrf_score,
        rerank_score=candidate.rerank_score,
        image_rank=candidate.image_rank,
        image_score=candidate.image_score,
        matched_image_id=candidate.matched_image_id,
        fusion_score=candidate.fusion_score,
        product=ProductSummary.model_validate(candidate.product),
    )


@router.post("", response_model=MultimodalSearchResponse)
def multimodal_search(
    request: MultimodalSearchRequest,
    service: Annotated[MultimodalSearchService, Depends(get_multimodal_search_service)],
    response: Response,
    cache: Annotated[ResponseCache, Depends(get_multimodal_cache)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MultimodalSearchResponse:
    key = cache_key("multimodal-search", request, settings)
    cached = cache.get(key)
    if cached is not None:
        try:
            result = MultimodalSearchResponse.model_validate_json(cached)
        except ValueError:
            cached = None
        else:
            response.headers["X-ShopLens-Cache"] = "HIT"
            metrics.counter(
                "shoplens_multimodal_cache_total",
                labels={"outcome": "hit"},
                help_text="Multimodal-search response cache outcomes",
            )
            return result
    response.headers["X-ShopLens-Cache"] = "MISS"
    metrics.counter(
        "shoplens_multimodal_cache_total",
        labels={"outcome": "miss"},
        help_text="Multimodal-search response cache outcomes",
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
    try:
        execution = service.search(asset_id=request.asset_id, query=request.query, filters=filters)
    except AssetNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="asset not found"
        ) from error
    offset = (request.page - 1) * request.page_size
    page_items = execution.items[offset : offset + request.page_size]
    result = MultimodalSearchResponse(
        retrieval_mode=execution.mode,
        query=request.query,
        asset_id=request.asset_id,
        applied_filters=request.filters,
        items=[_item(candidate, offset + index) for index, candidate in enumerate(page_items, 1)],
        page=request.page,
        page_size=request.page_size,
        total=execution.total,
        trace=execution.trace,
    )
    cache.set(key, result.model_dump_json())
    return result
