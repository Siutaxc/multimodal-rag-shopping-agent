"""Strict external-record and ingestion-report schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.domain.products import IngestionStatus, ReviewTopic


def _reject_float(value: object) -> object:
    if isinstance(value, float):
        raise ValueError("floating-point input is forbidden; use an exact string or integer")
    return value


class StrictInputModel(BaseModel):
    """Reject unknown source fields rather than silently dropping possible facts."""

    model_config = ConfigDict(extra="forbid")


class MeasurementInput(StrictInputModel):
    """A source measurement whose unit must be normalized explicitly."""

    value: Decimal
    unit: str = Field(min_length=1, max_length=32)

    @field_validator("value", mode="before")
    @classmethod
    def reject_binary_float(cls, value: object) -> object:
        return _reject_float(value)


class ImageInput(StrictInputModel):
    """A fixture-local image reference; remote downloads are not performed here."""

    local_path: str = Field(min_length=1, max_length=500)
    media_type: str = Field(min_length=1, max_length=100)
    source_url: HttpUrl | None = None
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    alt_text: str | None = Field(default=None, max_length=500)


class ReviewEvidenceInput(StrictInputModel):
    """A source-attributed review excerpt; it remains untrusted content."""

    source_review_id: str = Field(min_length=1, max_length=255)
    topic: ReviewTopic
    excerpt: str = Field(min_length=1, max_length=4000)
    rating: Decimal | None = Field(default=None, ge=0, le=5)
    reviewed_at: datetime | None = None
    source_url: HttpUrl | None = None

    @field_validator("rating", mode="before")
    @classmethod
    def reject_binary_float(cls, value: object) -> object:
        return _reject_float(value)

    @field_validator("reviewed_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("reviewed_at must include a timezone")
        return value


class RawProductRecord(StrictInputModel):
    """One untrusted product record before cleaning and unit conversion."""

    source_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    brand: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=10000)
    price_amount: Decimal
    currency: str = Field(min_length=3, max_length=3)
    price_observed_at: datetime
    wireless: bool | str | None = None
    anc: bool | str | None = None
    battery_life: MeasurementInput | None = None
    weight: MeasurementInput | None = None
    colors: list[str] = Field(default_factory=list, max_length=20)
    codecs: list[str] = Field(default_factory=list, max_length=20)
    water_resistance: str | None = Field(default=None, max_length=32)
    microphone: str | None = Field(default=None, max_length=2000)
    source_url: HttpUrl
    images: list[ImageInput] = Field(default_factory=list, max_length=12)
    reviews: list[ReviewEvidenceInput] = Field(default_factory=list, max_length=100)

    @field_validator("price_amount", mode="before")
    @classmethod
    def reject_binary_float(cls, value: object) -> object:
        return _reject_float(value)

    @field_validator("price_observed_at")
    @classmethod
    def require_price_timezone(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("price_observed_at must include a timezone")
        return value


class FixtureBatch(StrictInputModel):
    """Metadata envelope and raw records for a reproducible fixture snapshot."""

    source_name: str = Field(min_length=1, max_length=120)
    source_version: str = Field(min_length=1, max_length=120)
    transformation_version: str = Field(min_length=1, max_length=120)
    acquired_at: datetime
    license: str = Field(min_length=1, max_length=500)
    records: list[dict[str, Any]] = Field(min_length=1, max_length=1000)

    @field_validator("acquired_at")
    @classmethod
    def require_acquired_timezone(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("acquired_at must include a timezone")
        return value


class IngestionError(BaseModel):
    """Stable, JSON-serializable failure details for one record."""

    record_index: int
    source_id: str | None
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)


class IngestionReport(BaseModel):
    """Counters and errors returned by the CLI and persisted in ingestion_jobs."""

    job_id: UUID
    status: IngestionStatus
    total: int
    succeeded: int
    failed: int
    skipped: int
    errors: list[IngestionError]
