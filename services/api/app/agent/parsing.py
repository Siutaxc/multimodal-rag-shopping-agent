"""Deterministic Chinese/English constraint parsing and conversation merging."""

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from uuid import UUID

from app.agent.schemas import AgentIntent, FilterField, ParsedTurn, SessionContext
from app.api.search import SearchFiltersInput
from app.domain.products import ProductCategory

_CATEGORY_ALIASES: tuple[tuple[ProductCategory, tuple[str, ...]], ...] = (
    (ProductCategory.SEMI_IN_EAR, ("半入耳", "semi-in-ear", "semi in ear")),
    (ProductCategory.BONE_CONDUCTION, ("骨传导", "bone conduction")),
    (ProductCategory.OPEN_EAR, ("开放式", "开放耳", "不入耳", "open-ear", "open ear")),
    (ProductCategory.OVER_EAR, ("头戴式", "头戴", "包耳", "over-ear", "over ear")),
    (ProductCategory.ON_EAR, ("贴耳式", "贴耳", "on-ear", "on ear")),
    (ProductCategory.IN_EAR, ("入耳式", "入耳", "in-ear", "in ear")),
)
_SOFT_PREFERENCES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("适合通勤", ("通勤", "地铁", "公交")),
    ("佩戴舒适", ("舒适", "戴眼镜", "不夹头", "久戴")),
    ("重视音质", ("音质", "声音", "人声", "低频")),
    ("重视通话", ("通话", "会议", "麦克风", "拾音")),
    ("适合运动", ("运动", "跑步", "健身", "户外")),
    ("适合游戏", ("游戏", "延迟", "电竞")),
    ("便携轻量", ("便携", "轻量", "轻便")),
)
_COLORS = ("黑色", "白色", "蓝色", "红色", "绿色", "灰色", "银色", "粉色", "紫色")
_CODECS = ("LDAC", "LHDC", "AAC", "SBC", "APTX HD", "APTX", "LC3")
_UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


class RuleConstraintParser:
    """Parse only reviewed fields; unmatched text remains a soft retrieval query."""

    identity = "shoplens/rule-constraints@stage6-v1"

    def parse(self, message: str) -> ParsedTurn:
        normalized = _normalize(message)
        intent = _intent(normalized)
        clear_all = bool(
            re.search(
                r"清除(?:全部|所有)?条件|重置(?:全部|所有)?条件|重新开始",
                normalized,
            )
        )
        clear_fields = _clear_fields(normalized)
        values: dict[str, object] = {}

        category = _category(normalized)
        if category is not None:
            values["category"] = category
        brand = _explicit_text(normalized, r"品牌\s*[:\uff1a]?\s*([a-z0-9][a-z0-9 _-]{1,30})")
        if brand is not None:
            values["brand"] = brand
        _parse_price(normalized, values)
        if "price_min" in values or "price_max" in values:
            values["currency"] = "CNY"

        if not _contains_any(normalized, ("降噪不限", "无降噪要求", "清除降噪")):
            if _contains_any(
                normalized,
                ("不要降噪", "不需要降噪", "不支持主动降噪", "关闭降噪"),
            ):
                values["anc"] = False
            elif _contains_any(normalized, ("主动降噪", "降噪", "anc")):
                values["anc"] = True

        if not _contains_any(normalized, ("连接不限", "无线不限", "清除连接")):
            if _contains_any(normalized, ("有线", "不要无线", "非无线")):
                values["wireless"] = False
            elif _contains_any(normalized, ("无线", "蓝牙", "wireless")):
                values["wireless"] = True

        battery = _number_before_or_after(
            normalized,
            r"续航(?:至少|不低于|超过|大于)?\s*",
            r"\s*(?:小时|h)(?:以上|起|至少)?",
        )
        if battery is not None:
            values["battery_hours_min"] = battery
        weight = _number_before_or_after(
            normalized,
            r"(?:重量|不超过|低于|轻于)\s*",
            r"\s*(?:克|g)(?:以内|以下)?",
        )
        if weight is not None:
            values["weight_grams_max"] = weight

        for color in _COLORS:
            if color in normalized:
                values["color"] = color
                break
        upper = normalized.upper()
        for codec in _CODECS:
            if re.search(rf"(?<![A-Z0-9]){re.escape(codec)}(?![A-Z0-9])", upper):
                values["codec"] = codec.replace(" ", "-")
                break
        water = re.search(r"\bIP\d{2}\b", upper)
        if water is not None:
            values["water_resistance"] = water.group(0)

        preferences = [
            label for label, aliases in _SOFT_PREFERENCES if _contains_any(normalized, aliases)
        ]
        referenced_ids = [UUID(value) for value in _UUID_PATTERN.findall(normalized)]
        return ParsedTurn(
            intent=intent,
            filters=SearchFiltersInput.model_validate(values),
            clear_fields=clear_fields,
            clear_all=clear_all,
            clear_soft_preferences=bool(
                re.search(r"清除(?:所有)?偏好|偏好不限|不保留偏好", normalized)
            ),
            soft_preferences=preferences,
            referenced_product_ids=referenced_ids,
        )


def merge_session_context(
    context: SessionContext | None,
    turn: ParsedTurn,
    *,
    explicit_filters: SearchFiltersInput | None = None,
    explicit_clear_fields: list[FilterField] | None = None,
) -> tuple[SearchFiltersInput, list[str]]:
    """Apply clear -> inherited values -> latest values -> explicit HTTP overrides."""

    inherited = (
        {} if context is None or turn.clear_all else context.filters.model_dump(exclude_none=True)
    )
    for field in turn.clear_fields:
        inherited.pop(field.value, None)
    inherited.update(turn.filters.model_dump(exclude_none=True))
    for field in explicit_clear_fields or []:
        inherited.pop(field.value, None)
    if explicit_filters is not None:
        inherited.update(explicit_filters.model_dump(exclude_none=True))
    filters = SearchFiltersInput.model_validate(inherited)

    preferences = [] if context is None or turn.clear_all else list(context.soft_preferences)
    if turn.clear_soft_preferences:
        preferences = []
    for preference in turn.soft_preferences:
        if preference not in preferences:
            preferences.append(preference)
    return filters, preferences[:12]


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def _intent(value: str) -> AgentIntent:
    if _contains_any(value, ("对比", "比较", "区别", "哪个好", "哪款好")):
        return AgentIntent.COMPARE
    if _contains_any(value, ("搜索", "查找", "找一下")):
        return AgentIntent.SEARCH
    return AgentIntent.RECOMMEND


def _category(value: str) -> ProductCategory | None:
    for category, aliases in _CATEGORY_ALIASES:
        if _contains_any(value, aliases):
            return category
    return None


def _clear_fields(value: str) -> list[FilterField]:
    patterns: tuple[tuple[FilterField, tuple[str, ...]], ...] = (
        (FilterField.PRICE_MIN, ("预算不限", "价格不限", "清除预算", "取消预算")),
        (FilterField.PRICE_MAX, ("预算不限", "价格不限", "清除预算", "取消预算")),
        (FilterField.CURRENCY, ("预算不限", "价格不限", "清除预算", "取消预算")),
        (FilterField.CATEGORY, ("类型不限", "品类不限", "清除类型")),
        (FilterField.BRAND, ("品牌不限", "清除品牌")),
        (FilterField.ANC, ("降噪不限", "无降噪要求", "清除降噪")),
        (FilterField.WIRELESS, ("连接不限", "无线不限", "清除连接")),
        (FilterField.BATTERY_HOURS_MIN, ("续航不限", "清除续航")),
        (FilterField.WEIGHT_GRAMS_MAX, ("重量不限", "清除重量")),
        (FilterField.COLOR, ("颜色不限", "清除颜色")),
        (FilterField.CODEC, ("编码不限", "codec不限", "清除编码")),
        (FilterField.WATER_RESISTANCE, ("防水不限", "清除防水")),
    )
    return [field for field, aliases in patterns if _contains_any(value, aliases)]


def _parse_price(value: str, output: dict[str, object]) -> None:
    number = r"(\d+(?:\.\d{1,2})?)"
    range_match = re.search(
        rf"{number}\s*(?:元|块|cny|rmb)?\s*(?:到|至|[-~])\s*{number}\s*(?:元|块|cny|rmb)",
        value,
    )
    if range_match is not None:
        minimum = _decimal(range_match.group(1))
        maximum = _decimal(range_match.group(2))
        if minimum is not None and maximum is not None:
            output["price_min"] = min(minimum, maximum)
            output["price_max"] = max(minimum, maximum)
        return
    maximum_patterns = (
        rf"(?:预算|价格)\s*(?:不超过|不高于|最高|上限|低于|少于)\s*{number}",
        rf"(?:不超过|不高于|最高|上限|低于|少于)\s*{number}\s*(?:元|块|cny|rmb)",
        rf"{number}\s*(?:元|块|cny|rmb)\s*(?:以内|以下|封顶)",
        rf"预算\s*(?:是|为|改成|调整为|换成|:|\uff1a)?\s*{number}\s*(?:元|块|cny|rmb)?",
    )
    for pattern in maximum_patterns:
        match = re.search(pattern, value)
        if match is not None:
            parsed = _decimal(match.group(1))
            if parsed is not None:
                output["price_max"] = parsed
            return
    minimum_patterns = (
        rf"(?:预算|价格)\s*(?:不低于|至少|最低|高于|超过)\s*{number}",
        rf"(?:不低于|至少|最低|高于|超过)\s*{number}\s*(?:元|块|cny|rmb)",
        rf"{number}\s*(?:元|块|cny|rmb)\s*(?:以上|起)",
    )
    for pattern in minimum_patterns:
        match = re.search(pattern, value)
        if match is not None:
            parsed = _decimal(match.group(1))
            if parsed is not None:
                output["price_min"] = parsed
            return


def _number_before_or_after(value: str, prefix: str, suffix: str) -> Decimal | None:
    number = r"(\d+(?:\.\d{1,2})?)"
    match = re.search(prefix + number + suffix, value)
    if match is None:
        match = re.search(number + suffix, value)
    return _decimal(match.group(1)) if match is not None else None


def _decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _explicit_text(value: str, pattern: str) -> str | None:
    match = re.search(pattern, value)
    return match.group(1).strip() if match is not None else None


def _contains_any(value: str, candidates: tuple[str, ...]) -> bool:
    return any(candidate.casefold() in value for candidate in candidates)
