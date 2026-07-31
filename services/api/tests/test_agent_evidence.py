"""Structured fact grounding, comparisons, and citation safety."""

from decimal import Decimal

import pytest
from app.agent.evidence import (
    build_comparison,
    build_evidence,
    build_recommendations,
    validate_citations,
)
from app.agent.schemas import AnswerPlan, PlannedRecommendation
from app.api.search import SearchFiltersInput

from .agent_helpers import make_product


@pytest.mark.parametrize("case", range(100))
def test_one_hundred_structured_price_facts_are_exact(case: int) -> None:
    price = Decimal(case + 1).quantize(Decimal("0.01"))
    product = make_product(case + 1, price=price, include_review=False)
    evidence = build_evidence([product])
    price_item = next(item for item in evidence if item.field == "price_amount")
    plan = AnswerPlan(
        recommendations=[
            PlannedRecommendation(
                product_id=product.id,
                evidence_ids=[price_item.id],
            )
        ]
    )
    recommendations = build_recommendations(
        [product],
        SearchFiltersInput(price_max="1000", currency="CNY"),
        evidence,
        plan,
    )

    assert price_item.value == str(price)
    assert recommendations[0].product.price_amount == price
    valid, _, errors = validate_citations(recommendations, None, evidence)
    assert valid is True
    assert errors == []


def test_comparison_marks_unknown_values_and_cites_every_cell() -> None:
    products = [make_product(1), make_product(2)]
    evidence = build_evidence(products)
    comparison = build_comparison(products)
    recommendations = build_recommendations(
        products,
        SearchFiltersInput(),
        evidence,
        AnswerPlan(
            recommendations=[
                PlannedRecommendation(
                    product_id=product.id,
                    evidence_ids=[f"fact:{product.id}:price_amount"],
                )
                for product in products
            ]
        ),
    )

    water_row = next(row for row in comparison.rows if row.field == "water_resistance")
    assert [value.value for value in water_row.values] == [None, None]
    valid, checked, errors = validate_citations(recommendations, comparison, evidence)
    assert valid is True
    assert checked >= len(comparison.rows) * 2
    assert errors == []
