"""Unit tests for exact, deterministic source normalization."""

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from app.domain.products import ProductCategory
from app.ingestion.normalization import normalize_product
from app.ingestion.schemas import FixtureBatch, RawProductRecord
from app.ingestion.service import load_fixture
from pydantic import ValidationError

FIXTURE_PATH = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "headphones.json"


@pytest.fixture(scope="module")
def fixture_batch() -> FixtureBatch:
    return FixtureBatch.model_validate(load_fixture(FIXTURE_PATH))


def normalized_record(batch: FixtureBatch, index: int) -> Any:
    record = RawProductRecord.model_validate(batch.records[index])
    return normalize_product(
        record,
        source_name=batch.source_name,
        source_version=batch.source_version,
        transformation_version=batch.transformation_version,
    )


def test_fixture_contains_24_synthetic_products(fixture_batch: FixtureBatch) -> None:
    assert len(fixture_batch.records) == 24
    assert fixture_batch.license.startswith("CC0-1.0")


def test_chinese_enums_booleans_and_units_are_normalized(fixture_batch: FixtureBatch) -> None:
    product = normalized_record(fixture_batch, 0)

    assert product.category == ProductCategory.OVER_EAR
    assert product.wireless is True
    assert product.anc is True
    assert product.battery_hours == Decimal("40.00")
    assert product.weight_grams == Decimal("245.00")
    assert product.currency == "CNY"


def test_minutes_and_kilograms_are_converted_exactly(fixture_batch: FixtureBatch) -> None:
    product = normalized_record(fixture_batch, 1)

    assert product.battery_hours == Decimal("55.00")
    assert product.weight_grams == Decimal("268.00")


def test_binary_float_price_is_rejected(fixture_batch: FixtureBatch) -> None:
    payload = deepcopy(fixture_batch.records[0])
    payload["price_amount"] = 899.0

    with pytest.raises(ValidationError, match="floating-point input is forbidden"):
        RawProductRecord.model_validate(payload)


@pytest.mark.parametrize(
    ("field_update", "expected_message"),
    [
        ({"price_amount": "-1.00"}, "price_amount must be non-negative"),
        ({"price_amount": "1.999"}, "at most 2 decimal places"),
        ({"category": "necklace"}, "category is unsupported"),
        ({"battery_life": {"value": "3", "unit": "days"}}, "unit is unsupported"),
        ({"anc": "maybe"}, "unsupported boolean value"),
    ],
)
def test_invalid_price_enum_unit_and_boolean_have_clear_errors(
    fixture_batch: FixtureBatch,
    field_update: dict[str, object],
    expected_message: str,
) -> None:
    payload = deepcopy(fixture_batch.records[0])
    payload.update(field_update)
    record = RawProductRecord.model_validate(payload)

    with pytest.raises(ValueError, match=expected_message):
        normalize_product(
            record,
            source_name=fixture_batch.source_name,
            source_version=fixture_batch.source_version,
            transformation_version=fixture_batch.transformation_version,
        )
