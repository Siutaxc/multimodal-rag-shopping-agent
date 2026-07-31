"""Product list, detail, and deterministic structured-filter endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.products import ProductFilters, ProductRepository, ProductSort
from app.db.session import get_db_session
from app.domain.products import ProductCategory, ReviewTopic

router = APIRouter(prefix="/products", tags=["products"])


class ProductSummary(BaseModel):
    """Structured facts used by product lists without generated claims."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    brand: str
    category: ProductCategory
    price_amount: Decimal
    currency: str
    price_observed_at: datetime
    wireless: bool | None
    anc: bool | None
    battery_hours: Decimal | None
    weight_grams: Decimal | None
    colors: list[str]
    codecs: list[str]
    water_resistance: str | None
    source_name: str
    source_url: str


class ProductImageResponse(BaseModel):
    """Metadata for a locally stored product image."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int
    storage_key: str
    source_url: str | None
    sha256: str
    media_type: str
    byte_size: int
    width: int | None
    height: int | None
    alt_text: str | None


class ReviewEvidenceResponse(BaseModel):
    """Source-attributed untrusted review evidence."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_name: str
    source_review_id: str
    topic: ReviewTopic
    excerpt: str
    rating: Decimal | None
    reviewed_at: datetime | None
    source_url: str | None


class ProductDetail(ProductSummary):
    """All stage-two product facts plus provenance and available evidence."""

    description: str | None
    microphone: str | None
    source_id: str
    source_version: str
    transformation_version: str
    images: list[ProductImageResponse]
    review_evidence: list[ReviewEvidenceResponse]
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """Stable page envelope with a database-derived total."""

    items: list[ProductSummary]
    page: int
    page_size: int
    total: int


def get_product_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> ProductRepository:
    return ProductRepository(session)


@router.get("", response_model=ProductListResponse, summary="List and filter products")
def list_products(
    repository: Annotated[ProductRepository, Depends(get_product_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: ProductCategory | None = None,
    brand: Annotated[str | None, Query(min_length=1, max_length=160)] = None,
    price_min: Annotated[Decimal | None, Query(ge=0, max_digits=12, decimal_places=2)] = None,
    price_max: Annotated[Decimal | None, Query(ge=0, max_digits=12, decimal_places=2)] = None,
    currency: Annotated[str | None, Query(min_length=3, max_length=3)] = None,
    wireless: bool | None = None,
    anc: bool | None = None,
    battery_hours_min: Annotated[
        Decimal | None, Query(gt=0, max_digits=7, decimal_places=2)
    ] = None,
    weight_grams_max: Annotated[Decimal | None, Query(gt=0, max_digits=9, decimal_places=2)] = None,
    color: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    codec: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    water_resistance: Annotated[str | None, Query(min_length=2, max_length=32)] = None,
    sort: ProductSort = ProductSort.NEWEST,
) -> ProductListResponse:
    if price_min is not None and price_max is not None and price_min > price_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="price_min must not exceed price_max",
        )
    filters = ProductFilters(
        page=page,
        page_size=page_size,
        category=category,
        brand=brand,
        price_min=price_min,
        price_max=price_max,
        currency=currency,
        wireless=wireless,
        anc=anc,
        battery_hours_min=battery_hours_min,
        weight_grams_max=weight_grams_max,
        color=color,
        codec=codec,
        water_resistance=water_resistance,
        sort=sort,
    )
    products, total = repository.list_products(filters)
    return ProductListResponse(
        items=[ProductSummary.model_validate(product) for product in products],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{product_id}", response_model=ProductDetail, summary="Get product facts and sources")
def get_product(
    product_id: UUID,
    repository: Annotated[ProductRepository, Depends(get_product_repository)],
) -> ProductDetail:
    product = repository.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")
    return ProductDetail.model_validate(product)
