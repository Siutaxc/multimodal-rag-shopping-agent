"""Parameterized product reads and deterministic structured filters."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.db.models import Product
from app.domain.products import ProductCategory


class ProductSort(StrEnum):
    """Reviewed sort modes exposed by the HTTP API."""

    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NEWEST = "newest"


@dataclass(frozen=True)
class ProductFilters:
    """Whitelisted hard filters; this type intentionally cannot carry SQL."""

    page: int = 1
    page_size: int = 20
    category: ProductCategory | None = None
    brand: str | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    currency: str | None = None
    wireless: bool | None = None
    anc: bool | None = None
    battery_hours_min: Decimal | None = None
    weight_grams_max: Decimal | None = None
    color: str | None = None
    codec: str | None = None
    water_resistance: str | None = None
    sort: ProductSort = ProductSort.NEWEST


class ProductRepository:
    """Read products with SQLAlchemy expressions and bound parameters only."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_products(self, filters: ProductFilters) -> tuple[list[Product], int]:
        clauses = product_filter_clauses(filters)

        total = self._session.scalar(select(func.count()).select_from(Product).where(*clauses))
        query: Select[tuple[Product]] = select(Product).where(*clauses)
        if filters.sort == ProductSort.PRICE_ASC:
            query = query.order_by(Product.price_amount.asc(), Product.id.asc())
        elif filters.sort == ProductSort.PRICE_DESC:
            query = query.order_by(Product.price_amount.desc(), Product.id.asc())
        else:
            query = query.order_by(Product.created_at.desc(), Product.id.asc())
        query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        return list(self._session.scalars(query).all()), int(total or 0)

    def get_product(self, product_id: UUID) -> Product | None:
        query = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.images),
                selectinload(Product.documents),
                selectinload(Product.review_evidence),
            )
        )
        return self._session.scalar(query)

    def get_products(self, product_ids: list[UUID]) -> list[Product]:
        """Load at most four complete evidence packages in caller-supplied order."""

        if not product_ids:
            return []
        if len(product_ids) > 4:
            raise ValueError("at most four product details may be loaded")
        query = (
            select(Product)
            .where(Product.id.in_(product_ids))
            .options(
                selectinload(Product.images),
                selectinload(Product.documents),
                selectinload(Product.review_evidence),
            )
        )
        by_id = {product.id: product for product in self._session.scalars(query).all()}
        return [by_id[product_id] for product_id in product_ids if product_id in by_id]


def product_filter_clauses(filters: ProductFilters) -> list[ColumnElement[bool]]:
    """Translate reviewed filter fields into parameterized SQLAlchemy expressions."""

    clauses: list[ColumnElement[bool]] = []
    if filters.category is not None:
        clauses.append(Product.category == filters.category)
    if filters.brand is not None:
        clauses.append(func.lower(Product.brand) == filters.brand.strip().casefold())
    if filters.price_min is not None:
        clauses.append(Product.price_amount >= filters.price_min)
    if filters.price_max is not None:
        clauses.append(Product.price_amount <= filters.price_max)
    if filters.currency is not None:
        clauses.append(Product.currency == filters.currency.upper())
    if filters.wireless is not None:
        clauses.append(Product.wireless.is_(filters.wireless))
    if filters.anc is not None:
        clauses.append(Product.anc.is_(filters.anc))
    if filters.battery_hours_min is not None:
        clauses.append(Product.battery_hours >= filters.battery_hours_min)
    if filters.weight_grams_max is not None:
        clauses.append(Product.weight_grams <= filters.weight_grams_max)
    if filters.color is not None:
        clauses.append(Product.colors.contains([filters.color.strip().casefold()]))
    if filters.codec is not None:
        clauses.append(Product.codecs.contains([filters.codec.strip().upper()]))
    if filters.water_resistance is not None:
        clauses.append(
            func.upper(Product.water_resistance) == filters.water_resistance.strip().upper()
        )
    return clauses
