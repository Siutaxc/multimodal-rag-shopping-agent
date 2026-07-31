"""Natural-language whitelist parsing and session mutation contracts."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.agent.parsing import RuleConstraintParser, merge_session_context
from app.agent.schemas import AgentIntent, FilterField, SessionContext
from app.api.search import SearchFiltersInput
from app.domain.products import ProductCategory


def test_rule_parser_extracts_only_whitelisted_hard_filters() -> None:
    parsed = RuleConstraintParser().parse(
        "预算 500 到 1000 元, 头戴式无线主动降噪, 续航至少 30 小时, "
        "重量 260g 以内, 黑色, LDAC, IP54, 适合地铁通勤且戴眼镜舒适"
    )

    assert parsed.intent == AgentIntent.RECOMMEND
    assert parsed.filters.category == ProductCategory.OVER_EAR
    assert parsed.filters.price_min == Decimal("500")
    assert parsed.filters.price_max == Decimal("1000")
    assert parsed.filters.currency == "CNY"
    assert parsed.filters.wireless is True
    assert parsed.filters.anc is True
    assert parsed.filters.battery_hours_min == Decimal("30")
    assert parsed.filters.weight_grams_max == Decimal("260")
    assert parsed.filters.color == "黑色"
    assert parsed.filters.codec == "LDAC"
    assert parsed.filters.water_resistance == "IP54"
    assert parsed.soft_preferences == ["适合通勤", "佩戴舒适"]


def test_latest_turn_overrides_inherits_and_clears_individual_conditions() -> None:
    session = SessionContext(
        session_id=uuid4(),
        filters=SearchFiltersInput(price_max="1000", currency="CNY", anc=True),
        soft_preferences=["适合通勤"],
        last_product_ids=[],
        updated_at=datetime.now(UTC),
    )
    turn = RuleConstraintParser().parse("预算改成 800 元, 降噪不限, 戴眼镜舒适")
    filters, preferences = merge_session_context(session, turn)

    assert filters.price_max == Decimal("800")
    assert filters.currency == "CNY"
    assert filters.anc is None
    assert preferences == ["适合通勤", "佩戴舒适"]

    filters, _ = merge_session_context(
        session,
        turn,
        explicit_filters=SearchFiltersInput(category="in_ear"),
        explicit_clear_fields=[FilterField.PRICE_MAX, FilterField.CURRENCY],
    )
    assert filters.category == ProductCategory.IN_EAR
    assert filters.price_max is None


def test_reset_and_compare_ids_are_explicit() -> None:
    left, right = uuid4(), uuid4()
    parsed = RuleConstraintParser().parse(f"清除所有条件, 对比 {left} 和 {right}")

    assert parsed.clear_all is True
    assert parsed.intent == AgentIntent.COMPARE
    assert parsed.referenced_product_ids == [left, right]


def test_battery_minimum_is_not_misclassified_as_a_minimum_price() -> None:
    parsed = RuleConstraintParser().parse("续航至少 7 小时, 其他条件保留")

    assert parsed.filters.battery_hours_min == Decimal("7")
    assert parsed.filters.price_min is None
    assert parsed.filters.currency is None
