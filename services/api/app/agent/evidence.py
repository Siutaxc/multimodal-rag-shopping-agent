"""Evidence package construction, deterministic rendering, and citation validation."""

from collections.abc import Iterable, Sequence
from decimal import Decimal

from app.agent.schemas import (
    AnswerPlan,
    ComparisonBundle,
    ComparisonRow,
    ComparisonValue,
    EvidenceItem,
    GroundedStatement,
    Recommendation,
)
from app.api.products import ProductSummary
from app.api.search import SearchFiltersInput
from app.db.models import Product

_FACT_FIELDS = (
    "title",
    "brand",
    "category",
    "price_amount",
    "currency",
    "price_observed_at",
    "wireless",
    "anc",
    "battery_hours",
    "weight_grams",
    "colors",
    "codecs",
    "water_resistance",
    "microphone",
)
_FIELD_LABELS = {
    "title": "商品",
    "brand": "品牌",
    "category": "类型",
    "price_amount": "价格",
    "currency": "币种",
    "price_observed_at": "价格快照",
    "wireless": "无线",
    "anc": "主动降噪",
    "battery_hours": "续航(小时)",
    "weight_grams": "重量(克)",
    "colors": "颜色",
    "codecs": "音频编码",
    "water_resistance": "防水",
    "microphone": "麦克风",
}
_TOPIC_LABELS = {
    "anc": "降噪",
    "comfort": "佩戴舒适度",
    "sound": "声音表现",
    "microphone": "通话",
    "battery": "续航",
    "other": "使用体验",
}


def build_evidence(products: Sequence[Product]) -> list[EvidenceItem]:
    """Create fact rows even for nulls so an unknown value is itself auditable."""

    items: list[EvidenceItem] = []
    for product in products:
        for field in _FACT_FIELDS:
            raw = getattr(product, field)
            value = _evidence_value(raw)
            items.append(
                EvidenceItem(
                    id=f"fact:{product.id}:{field}",
                    product_id=product.id,
                    kind="product_fact",
                    field=field,
                    value=value,
                    available=raw is not None,
                    source_name=product.source_name,
                    source_url=product.source_url,
                    observed_at=(
                        product.price_observed_at
                        if field in {"price_amount", "currency", "price_observed_at"}
                        else None
                    ),
                )
            )
        for review in product.review_evidence:
            items.append(
                EvidenceItem(
                    id=f"review:{review.id}",
                    product_id=product.id,
                    kind="review",
                    field=review.topic.value,
                    value=str(review.rating) if review.rating is not None else None,
                    source_name=review.source_name,
                    source_url=review.source_url,
                    observed_at=review.reviewed_at,
                    excerpt=review.excerpt,
                    untrusted_content=True,
                )
            )
    return items


def build_recommendations(
    products: Sequence[Product],
    filters: SearchFiltersInput,
    evidence: Sequence[EvidenceItem],
    plan: AnswerPlan,
) -> list[Recommendation]:
    by_id = {item.id: item for item in evidence}
    planned = {item.product_id: item.evidence_ids for item in plan.recommendations}
    recommendations: list[Recommendation] = []
    for rank, product in enumerate(products, start=1):
        matched = _matched_requirements(product, filters)
        reasons = [
            _reason_statement(evidence_id, by_id) for evidence_id in planned.get(product.id, [])
        ]
        if not reasons:
            reasons = [
                GroundedStatement(
                    text="价格与来源快照可核验。",
                    evidence_ids=[f"fact:{product.id}:price_amount"],
                )
            ]
        tradeoffs = _unknown_tradeoffs(product)
        citations = _dedupe(
            evidence_id
            for statement in [*matched, *reasons, *tradeoffs]
            for evidence_id in statement.evidence_ids
        )
        recommendations.append(
            Recommendation(
                product=ProductSummary.model_validate(product),
                rank=rank,
                matched_requirements=matched,
                reasons=reasons,
                tradeoffs=tradeoffs,
                evidence_ids=citations,
            )
        )
    return recommendations


def build_comparison(products: Sequence[Product]) -> ComparisonBundle:
    if not 2 <= len(products) <= 4:
        raise ValueError("comparison requires two to four products")
    fields = (
        "price_amount",
        "currency",
        "category",
        "wireless",
        "anc",
        "battery_hours",
        "weight_grams",
        "colors",
        "codecs",
        "water_resistance",
        "microphone",
    )
    return ComparisonBundle(
        product_ids=[product.id for product in products],
        rows=[
            ComparisonRow(
                field=field,
                label=_FIELD_LABELS[field],
                values=[
                    ComparisonValue(
                        product_id=product.id,
                        value=_evidence_value(getattr(product, field)),
                        evidence_id=f"fact:{product.id}:{field}",
                    )
                    for product in products
                ],
            )
            for field in fields
        ],
    )


def validate_citations(
    recommendations: Sequence[Recommendation],
    comparison: ComparisonBundle | None,
    evidence: Sequence[EvidenceItem],
) -> tuple[bool, int, list[str]]:
    index = {item.id: item for item in evidence}
    errors: list[str] = []
    checked = 0
    for recommendation in recommendations:
        for statement in [
            *recommendation.matched_requirements,
            *recommendation.reasons,
            *recommendation.tradeoffs,
        ]:
            checked += 1
            if not statement.evidence_ids:
                errors.append(f"statement_without_evidence:{recommendation.product.id}")
            for evidence_id in statement.evidence_ids:
                item = index.get(evidence_id)
                if item is None:
                    errors.append(f"unknown_evidence:{evidence_id}")
                elif item.product_id != recommendation.product.id:
                    errors.append(f"cross_product_evidence:{evidence_id}")
        if set(recommendation.evidence_ids) != {
            evidence_id
            for statement in [
                *recommendation.matched_requirements,
                *recommendation.reasons,
                *recommendation.tradeoffs,
            ]
            for evidence_id in statement.evidence_ids
        }:
            errors.append(f"recommendation_evidence_mismatch:{recommendation.product.id}")
    if comparison is not None:
        for row in comparison.rows:
            for value in row.values:
                checked += 1
                item = index.get(value.evidence_id)
                if item is None:
                    errors.append(f"unknown_comparison_evidence:{value.evidence_id}")
                elif item.product_id != value.product_id or item.field != row.field:
                    errors.append(f"invalid_comparison_evidence:{value.evidence_id}")
    return not errors, checked, errors


def safe_answer_text(
    recommendations: Sequence[Recommendation],
    *,
    comparison: ComparisonBundle | None,
    degraded: bool,
) -> str:
    if not recommendations:
        return "当前条件下没有检索到商品, 你可以修改硬条件后再试。"
    prefix = "回答生成已降级, " if degraded else ""
    if comparison is not None:
        return (
            f"{prefix}已按同一组结构化字段比较 {len(recommendations)} 件商品, "
            "缺失值标记为暂无可靠数据。"
        )
    return (
        f"{prefix}找到 {len(recommendations)} 件满足当前硬条件的候选, "
        "价格和参数均来自带来源的商品记录。"
    )


def _matched_requirements(product: Product, filters: SearchFiltersInput) -> list[GroundedStatement]:
    statements: list[GroundedStatement] = []
    if filters.category is not None:
        statements.append(_fact_statement(product, "category", f"类型为 {product.category.value}"))
    if filters.brand is not None:
        statements.append(_fact_statement(product, "brand", f"品牌为 {product.brand}"))
    if filters.price_max is not None:
        statements.append(
            _fact_statement(
                product,
                "price_amount",
                (
                    f"价格 {product.price_amount} {product.currency}, 不超过 "
                    f"{filters.price_max} {filters.currency or product.currency}"
                ),
            )
        )
    if filters.price_min is not None:
        statements.append(
            _fact_statement(
                product,
                "price_amount",
                (
                    f"价格 {product.price_amount} {product.currency}, 不低于 "
                    f"{filters.price_min} {filters.currency or product.currency}"
                ),
            )
        )
    if filters.wireless is not None:
        statements.append(
            _fact_statement(
                product,
                "wireless",
                "支持无线连接" if product.wireless else "采用有线连接",
            )
        )
    if filters.anc is not None:
        statements.append(
            _fact_statement(product, "anc", "支持主动降噪" if product.anc else "不支持主动降噪")
        )
    if filters.battery_hours_min is not None:
        statements.append(
            _fact_statement(product, "battery_hours", f"标称续航 {product.battery_hours} 小时")
        )
    if filters.weight_grams_max is not None:
        statements.append(
            _fact_statement(product, "weight_grams", f"重量 {product.weight_grams} 克")
        )
    if filters.color is not None:
        statements.append(_fact_statement(product, "colors", f"提供 {filters.color}"))
    if filters.codec is not None:
        statements.append(_fact_statement(product, "codecs", f"支持 {filters.codec.upper()}"))
    if filters.water_resistance is not None:
        statements.append(
            _fact_statement(product, "water_resistance", f"防水等级 {product.water_resistance}")
        )
    return statements


def _fact_statement(product: Product, field: str, text: str) -> GroundedStatement:
    return GroundedStatement(text=text, evidence_ids=[f"fact:{product.id}:{field}"])


def _reason_statement(evidence_id: str, index: dict[str, EvidenceItem]) -> GroundedStatement:
    item = index.get(evidence_id)
    if item is None:
        return GroundedStatement(text="所选证据不可用。", evidence_ids=[evidence_id])
    if item.kind == "review":
        topic = _TOPIC_LABELS.get(item.field, "使用体验")
        return GroundedStatement(
            text=f"有一条带来源的用户评价涉及{topic}; 该结论属于用户评价。",
            evidence_ids=[evidence_id],
        )
    label = _FIELD_LABELS.get(item.field, item.field)
    return GroundedStatement(
        text=f"{label}记录可从商品来源核验。",
        evidence_ids=[evidence_id],
    )


def _unknown_tradeoffs(product: Product) -> list[GroundedStatement]:
    statements: list[GroundedStatement] = []
    for field in ("battery_hours", "weight_grams", "water_resistance", "microphone"):
        if getattr(product, field) is None:
            statements.append(
                GroundedStatement(
                    text=f"{_FIELD_LABELS[field]}暂无可靠数据。",
                    evidence_ids=[f"fact:{product.id}:{field}"],
                )
            )
    return statements


def _evidence_value(value: object) -> str | bool | list[str] | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, list):
        return [str(item) for item in value]
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        formatted = isoformat()
        return formatted if isinstance(formatted, str) else str(value)
    return str(value)


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
