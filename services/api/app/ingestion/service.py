"""Audited, record-isolated, and idempotent fixture ingestion."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    IngestionJob,
    Product,
    ProductDocument,
    ProductImage,
    ReviewEvidence,
)
from app.domain.products import DocumentType, IngestionStatus
from app.ingestion.normalization import NormalizedProduct, normalize_product
from app.ingestion.schemas import (
    FixtureBatch,
    IngestionError,
    IngestionReport,
    RawProductRecord,
)
from app.providers.storage import ObjectStorage
from app.retrieval.documents import build_lexical_text

PersistOutcome = Literal["succeeded", "skipped"]


class IngestionService:
    """Import a small trusted fixture envelope while treating every record as untrusted."""

    def __init__(self, session: Session, storage: ObjectStorage | None = None) -> None:
        self._session = session
        self._storage = storage

    def import_payload(self, payload: dict[str, Any], *, fixture_root: Path) -> IngestionReport:
        """Validate batch metadata, isolate bad records, and persist final counters."""

        batch = FixtureBatch.model_validate(payload)
        batch_key = _batch_key(batch)
        job = IngestionJob(
            batch_key=batch_key,
            source_name=batch.source_name,
            source_version=batch.source_version,
            transformation_version=batch.transformation_version,
            status=IngestionStatus.RUNNING,
            total_count=len(batch.records),
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            errors=[],
        )
        self._session.add(job)
        self._session.commit()

        succeeded = 0
        skipped = 0
        errors: list[IngestionError] = []
        for index, raw_payload in enumerate(batch.records):
            source_id = _source_id_from_payload(raw_payload)
            try:
                raw_record = RawProductRecord.model_validate(raw_payload)
                product = normalize_product(
                    raw_record,
                    source_name=batch.source_name,
                    source_version=batch.source_version,
                    transformation_version=batch.transformation_version,
                )
                outcome = self._persist_product(
                    product,
                    batch=batch,
                    fixture_root=fixture_root,
                )
                if outcome == "succeeded":
                    succeeded += 1
                else:
                    skipped += 1
            except ValidationError as error:
                self._session.rollback()
                errors.append(
                    IngestionError(
                        record_index=index,
                        source_id=source_id,
                        message="record validation failed",
                        details=error.errors(
                            include_url=False, include_context=False, include_input=False
                        ),
                    )
                )
            except (OSError, SQLAlchemyError, ValueError) as error:
                self._session.rollback()
                errors.append(
                    IngestionError(
                        record_index=index,
                        source_id=source_id,
                        message=str(error),
                    )
                )

        status = _final_status(succeeded=succeeded, skipped=skipped, failed=len(errors))
        persisted_job = self._session.get(IngestionJob, job.id)
        if persisted_job is None:
            raise RuntimeError("ingestion job disappeared before counters were finalized")
        persisted_job.status = status
        persisted_job.succeeded_count = succeeded
        persisted_job.skipped_count = skipped
        persisted_job.failed_count = len(errors)
        persisted_job.errors = [error.model_dump(mode="json") for error in errors]
        persisted_job.finished_at = datetime.now(UTC)
        self._session.commit()

        return IngestionReport(
            job_id=persisted_job.id,
            status=status,
            total=len(batch.records),
            succeeded=succeeded,
            failed=len(errors),
            skipped=skipped,
            errors=errors,
        )

    def _persist_product(
        self,
        normalized: NormalizedProduct,
        *,
        batch: FixtureBatch,
        fixture_root: Path,
    ) -> PersistOutcome:
        duplicate = self._session.scalar(
            select(Product)
            .where(Product.idempotency_key == normalized.idempotency_key)
            .options(selectinload(Product.images))
        )
        if duplicate is not None:
            if not duplicate.images and self._fixture_has_images(normalized, fixture_root):
                self._populate_images(duplicate, normalized=normalized, fixture_root=fixture_root)
                self._commit_or_skip_race()
                return "succeeded"
            return "skipped"

        existing_source = self._session.scalar(
            select(Product)
            .where(
                Product.source_name == batch.source_name,
                Product.source_id == normalized.source_id,
            )
            .options(
                selectinload(Product.images),
                selectinload(Product.documents),
                selectinload(Product.review_evidence),
            )
        )
        if existing_source is not None:
            self._assign_product(existing_source, normalized=normalized, batch=batch)
            existing_source.images.clear()
            existing_source.documents.clear()
            existing_source.review_evidence.clear()
            self._session.flush()
            self._populate_children(
                existing_source,
                normalized=normalized,
                batch=batch,
                fixture_root=fixture_root,
            )
            self._commit_or_skip_race()
            return "succeeded"

        duplicate_identity = self._session.scalar(
            select(Product.id).where(Product.dedupe_key == normalized.dedupe_key)
        )
        if duplicate_identity is not None:
            return "skipped"

        product = Product()
        self._assign_product(product, normalized=normalized, batch=batch)
        self._populate_children(
            product,
            normalized=normalized,
            batch=batch,
            fixture_root=fixture_root,
        )
        self._session.add(product)
        self._commit_or_skip_race()
        return "succeeded"

    def _assign_product(
        self,
        product: Product,
        *,
        normalized: NormalizedProduct,
        batch: FixtureBatch,
    ) -> None:
        product.source_name = batch.source_name
        product.source_id = normalized.source_id
        product.source_version = batch.source_version
        product.transformation_version = batch.transformation_version
        product.idempotency_key = normalized.idempotency_key
        product.dedupe_key = normalized.dedupe_key
        product.title = normalized.title
        product.brand = normalized.brand
        product.category = normalized.category
        product.description = normalized.description
        product.price_amount = normalized.price_amount
        product.currency = normalized.currency
        product.price_observed_at = normalized.price_observed_at
        product.wireless = normalized.wireless
        product.anc = normalized.anc
        product.battery_hours = normalized.battery_hours
        product.weight_grams = normalized.weight_grams
        product.colors = normalized.colors
        product.codecs = normalized.codecs
        product.water_resistance = normalized.water_resistance
        product.microphone = normalized.microphone
        product.source_url = normalized.source_url

    def _populate_children(
        self,
        product: Product,
        *,
        normalized: NormalizedProduct,
        batch: FixtureBatch,
        fixture_root: Path,
    ) -> None:
        product.documents.append(
            ProductDocument(
                document_type=DocumentType.MAIN,
                document_version=batch.transformation_version,
                language="zh-CN",
                content=_main_document(normalized, source_name=batch.source_name),
                search_text=build_lexical_text(normalized),
            )
        )
        for review in normalized.reviews:
            product.review_evidence.append(
                ReviewEvidence(
                    source_name=batch.source_name,
                    source_review_id=review.source_review_id,
                    topic=review.topic,
                    excerpt=review.excerpt.strip(),
                    rating=review.rating,
                    reviewed_at=(
                        review.reviewed_at.astimezone(UTC)
                        if review.reviewed_at is not None
                        else None
                    ),
                    source_url=str(review.source_url) if review.source_url is not None else None,
                )
            )
        self._populate_images(product, normalized=normalized, fixture_root=fixture_root)

    def _fixture_has_images(self, normalized: NormalizedProduct, fixture_root: Path) -> bool:
        return (
            bool(normalized.images)
            or (fixture_root.resolve() / "images" / f"{normalized.source_id}.png").is_file()
        )

    def _populate_images(
        self, product: Product, *, normalized: NormalizedProduct, fixture_root: Path
    ) -> None:
        if normalized.images and self._storage is None:
            raise ValueError("records with images require an ObjectStorage provider")
        fixture_root_resolved = fixture_root.resolve()
        for position, image in enumerate(normalized.images):
            source_path = (fixture_root_resolved / image.local_path).resolve()
            if not source_path.is_relative_to(fixture_root_resolved):
                raise ValueError("image local_path escapes the fixture directory")
            assert self._storage is not None
            stored = self._storage.put_file(source_path, image.media_type)
            product.images.append(
                ProductImage(
                    position=position,
                    storage_key=stored.key,
                    source_url=str(image.source_url) if image.source_url is not None else None,
                    sha256=stored.sha256,
                    media_type=stored.media_type,
                    byte_size=stored.byte_size,
                    width=image.width,
                    height=image.height,
                    alt_text=image.alt_text,
                )
            )
        if not normalized.images:
            generated_fixture_image = (
                fixture_root_resolved / "images" / f"{normalized.source_id}.png"
            )
            if generated_fixture_image.is_file():
                if self._storage is None:
                    raise ValueError("records with generated fixture images require ObjectStorage")
                stored = self._storage.put_file(generated_fixture_image, "image/png")
                product.images.append(
                    ProductImage(
                        position=0,
                        storage_key=stored.key,
                        source_url=None,
                        sha256=stored.sha256,
                        media_type=stored.media_type,
                        byte_size=stored.byte_size,
                        width=320,
                        height=320,
                        alt_text=f"{normalized.title} deterministic fixture artwork",
                    )
                )

    def _commit_or_skip_race(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise ValueError("record conflicts with an existing unique identity") from error


def load_fixture(path: Path) -> dict[str, Any]:
    """Load one UTF-8 JSON object without accepting an arbitrary top-level type."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"fixture could not be read: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError("fixture root must be a JSON object")
    return raw


def _source_id_from_payload(payload: dict[str, Any]) -> str | None:
    value = payload.get("source_id")
    return value if isinstance(value, str) else None


def _batch_key(batch: FixtureBatch) -> str:
    text = "\x1f".join((batch.source_name, batch.source_version, batch.transformation_version))
    return hashlib.sha256(text.casefold().encode("utf-8")).hexdigest()


def _final_status(*, succeeded: int, skipped: int, failed: int) -> IngestionStatus:
    if failed == 0:
        return IngestionStatus.SUCCESS
    if succeeded + skipped > 0:
        return IngestionStatus.PARTIAL
    return IngestionStatus.FAILED


def _main_document(product: NormalizedProduct, *, source_name: str) -> str:
    facts = [
        f"品牌: {product.brand}",
        f"商品: {product.title}",
        f"类型: {product.category.value}",
        f"价格: {product.price_amount} {product.currency}",
        f"价格观测时间: {product.price_observed_at.isoformat()}",
        f"来源: {source_name}",
    ]
    if product.anc is not None:
        facts.append(f"主动降噪: {'支持' if product.anc else '不支持'}")
    if product.battery_hours is not None:
        facts.append(f"续航: {product.battery_hours} 小时")
    if product.weight_grams is not None:
        facts.append(f"重量: {product.weight_grams} 克")
    if product.colors:
        facts.append(f"颜色: {'、'.join(product.colors)}")
    if product.description is not None:
        facts.append(f"描述: {product.description}")
    return "\n".join(facts)
