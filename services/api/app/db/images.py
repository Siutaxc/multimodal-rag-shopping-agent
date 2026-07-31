"""Uploaded asset reads and exact-version pgvector image retrieval."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import ImageEmbedding, Product, ProductImage, UploadedImageAsset
from app.db.products import ProductFilters, product_filter_clauses


class UploadedImageAssetRepository:
    """Persist and resolve sanitized assets without exposing storage paths to clients."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, asset_id: UUID) -> UploadedImageAsset | None:
        return self._session.get(UploadedImageAsset, asset_id)

    def find_by_content_sha256(self, digest: str) -> UploadedImageAsset | None:
        return self._session.scalar(
            select(UploadedImageAsset).where(UploadedImageAsset.content_sha256 == digest)
        )

    def add(self, asset: UploadedImageAsset) -> UploadedImageAsset:
        self._session.add(asset)
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise
        self._session.refresh(asset)
        return asset


@dataclass(frozen=True)
class ImageSearchHit:
    """One product image match from an exact vector identity."""

    product: Product
    image_id: UUID
    image_score: float
    representation_version: str


class ImageSearchRepository:
    """Apply the same whitelisted hard filters before cosine image ranking."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def search(
        self,
        query_vector: list[float],
        filters: ProductFilters,
        *,
        model_name: str,
        model_version: str,
        dimension: int,
        representation_version: str,
        limit: int,
    ) -> tuple[list[ImageSearchHit], int]:
        distance = ImageEmbedding.embedding.cosine_distance(query_vector).label("distance")
        clauses = [
            ImageEmbedding.model_name == model_name,
            ImageEmbedding.model_version == model_version,
            ImageEmbedding.dimension == dimension,
            ImageEmbedding.representation_version == representation_version,
            ImageEmbedding.status == "ready",
            ImageEmbedding.embedding.is_not(None),
            *product_filter_clauses(filters),
        ]
        total = self._session.scalar(
            select(func.count(func.distinct(Product.id)))
            .join(ProductImage, ProductImage.product_id == Product.id)
            .join(ImageEmbedding, ImageEmbedding.image_id == ProductImage.id)
            .where(*clauses)
        )
        rows = self._session.execute(
            select(Product, ProductImage.id, distance)
            .join(ProductImage, ProductImage.product_id == Product.id)
            .join(ImageEmbedding, ImageEmbedding.image_id == ProductImage.id)
            .where(*clauses)
            .order_by(distance.asc(), Product.title.asc(), ProductImage.position.asc())
            .limit(limit * 4)
        ).all()
        hits: list[ImageSearchHit] = []
        seen: set[UUID] = set()
        for product, image_id, raw_distance in rows:
            if product.id in seen:
                continue
            seen.add(product.id)
            hits.append(
                ImageSearchHit(
                    product=product,
                    image_id=image_id,
                    image_score=max(-1.0, min(1.0, 1.0 - float(raw_distance))),
                    representation_version=representation_version,
                )
            )
            if len(hits) == limit:
                break
        return hits, int(total or 0)
