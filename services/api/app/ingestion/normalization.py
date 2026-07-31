"""Deterministic cleaning, enum mapping, exact units, and identity hashes."""

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.domain.products import ProductCategory
from app.ingestion.schemas import ImageInput, RawProductRecord, ReviewEvidenceInput

_SPACE_PATTERN = re.compile(r"\s+")
_CATEGORY_ALIASES = {
    "in_ear": ProductCategory.IN_EAR,
    "in-ear": ProductCategory.IN_EAR,
    "入耳式": ProductCategory.IN_EAR,
    "semi_in_ear": ProductCategory.SEMI_IN_EAR,
    "semi-in-ear": ProductCategory.SEMI_IN_EAR,
    "半入耳式": ProductCategory.SEMI_IN_EAR,
    "over_ear": ProductCategory.OVER_EAR,
    "over-ear": ProductCategory.OVER_EAR,
    "头戴式": ProductCategory.OVER_EAR,
    "on_ear": ProductCategory.ON_EAR,
    "on-ear": ProductCategory.ON_EAR,
    "贴耳式": ProductCategory.ON_EAR,
    "bone_conduction": ProductCategory.BONE_CONDUCTION,
    "bone-conduction": ProductCategory.BONE_CONDUCTION,
    "骨传导": ProductCategory.BONE_CONDUCTION,
    "open_ear": ProductCategory.OPEN_EAR,
    "open-ear": ProductCategory.OPEN_EAR,
    "开放式": ProductCategory.OPEN_EAR,
}
_TRUE_VALUES = {"true", "yes", "1", "是", "支持", "有"}
_FALSE_VALUES = {"false", "no", "0", "否", "不支持", "无"}
_CURRENCIES = {"CNY", "USD", "EUR", "GBP", "JPY"}
_HOUR_UNITS = {"h", "hr", "hour", "hours", "小时"}
_MINUTE_UNITS = {"min", "minute", "minutes", "分钟"}
_GRAM_UNITS = {"g", "gram", "grams", "克"}
_KILOGRAM_UNITS = {"kg", "kilogram", "kilograms", "千克", "公斤"}


@dataclass(frozen=True)
class NormalizedProduct:
    """Canonical values ready for parameterized persistence."""

    source_id: str
    title: str
    brand: str
    category: ProductCategory
    description: str | None
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
    microphone: str | None
    source_url: str
    images: list[ImageInput]
    reviews: list[ReviewEvidenceInput]
    idempotency_key: str
    dedupe_key: str


def clean_text(value: str, *, field: str) -> str:
    """Trim and collapse whitespace while preserving source text semantics."""

    cleaned = _SPACE_PATTERN.sub(" ", value).strip()
    if not cleaned:
        raise ValueError(f"{field} must not be blank")
    return cleaned


def _optional_text(value: str | None, *, field: str) -> str | None:
    return None if value is None else clean_text(value, field=field)


def _exact_decimal(
    value: Decimal, *, field: str, scale: int = 2, allow_rounding: bool = False
) -> Decimal:
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    quantum = Decimal(1).scaleb(-scale)
    try:
        normalized = value.quantize(quantum, rounding=ROUND_HALF_UP)
    except InvalidOperation as error:
        raise ValueError(f"{field} is outside the supported range") from error
    if not allow_rounding and normalized != value:
        raise ValueError(f"{field} supports at most {scale} decimal places")
    return normalized


def _normalize_bool(value: bool | str | None, *, field: str) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    normalized = clean_text(value, field=field).casefold()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"{field} has unsupported boolean value: {value}")


def _normalize_battery(record: RawProductRecord) -> Decimal | None:
    measurement = record.battery_life
    if measurement is None:
        return None
    if measurement.value <= 0:
        raise ValueError("battery_life.value must be positive")
    unit = measurement.unit.strip().casefold()
    if unit in _HOUR_UNITS:
        hours = measurement.value
    elif unit in _MINUTE_UNITS:
        hours = measurement.value / Decimal(60)
    else:
        raise ValueError(f"battery_life.unit is unsupported: {measurement.unit}")
    return _exact_decimal(hours, field="battery_hours", allow_rounding=True)


def _normalize_weight(record: RawProductRecord) -> Decimal | None:
    measurement = record.weight
    if measurement is None:
        return None
    if measurement.value <= 0:
        raise ValueError("weight.value must be positive")
    unit = measurement.unit.strip().casefold()
    if unit in _GRAM_UNITS:
        grams = measurement.value
    elif unit in _KILOGRAM_UNITS:
        grams = measurement.value * Decimal(1000)
    else:
        raise ValueError(f"weight.unit is unsupported: {measurement.unit}")
    return _exact_decimal(grams, field="weight_grams", allow_rounding=True)


def _unique_clean(values: list[str], *, field: str, uppercase: bool = False) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        cleaned = clean_text(raw, field=field)
        normalized = cleaned.upper() if uppercase else cleaned.casefold()
        if normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def _hash_parts(*parts: str) -> str:
    encoded = "\x1f".join(part.casefold() for part in parts).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_product(
    record: RawProductRecord,
    *,
    source_name: str,
    source_version: str,
    transformation_version: str,
) -> NormalizedProduct:
    """Normalize a validated raw record without guessing missing facts."""

    title = clean_text(record.title, field="title")
    brand = clean_text(record.brand, field="brand")
    category_key = clean_text(record.category, field="category").casefold()
    category = _CATEGORY_ALIASES.get(category_key)
    if category is None:
        raise ValueError(f"category is unsupported: {record.category}")

    amount = _exact_decimal(record.price_amount, field="price_amount")
    if amount < 0:
        raise ValueError("price_amount must be non-negative")
    currency = record.currency.upper()
    if currency not in _CURRENCIES:
        raise ValueError(f"currency is unsupported: {record.currency}")

    source_id = clean_text(record.source_id, field="source_id")
    return NormalizedProduct(
        source_id=source_id,
        title=title,
        brand=brand,
        category=category,
        description=_optional_text(record.description, field="description"),
        price_amount=amount,
        currency=currency,
        price_observed_at=record.price_observed_at.astimezone(UTC),
        wireless=_normalize_bool(record.wireless, field="wireless"),
        anc=_normalize_bool(record.anc, field="anc"),
        battery_hours=_normalize_battery(record),
        weight_grams=_normalize_weight(record),
        colors=_unique_clean(record.colors, field="colors"),
        codecs=_unique_clean(record.codecs, field="codecs", uppercase=True),
        water_resistance=_optional_text(record.water_resistance, field="water_resistance"),
        microphone=_optional_text(record.microphone, field="microphone"),
        source_url=str(record.source_url),
        images=record.images,
        reviews=record.reviews,
        idempotency_key=_hash_parts(source_name, source_id, source_version, transformation_version),
        dedupe_key=_hash_parts(brand, title, category.value),
    )
