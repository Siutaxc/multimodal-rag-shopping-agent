"""Build stable lexical documents without generated claims or inferred facts."""

from app.domain.products import ProductCategory
from app.ingestion.normalization import NormalizedProduct

LEXICAL_DOCUMENT_VERSION = "stage3-lexical-v1"

_DESCRIPTION_TERMS = (
    "通勤",
    "办公",
    "户外",
    "运动",
    "游泳",
    "室内",
    "便携",
    "旅行",
    "长续航",
    "轻量",
    "可折叠",
    "耳夹",
    "充电盒",
)

_CATEGORY_ALIASES: dict[ProductCategory, tuple[str, ...]] = {
    ProductCategory.IN_EAR: ("in ear", "in-ear", "入耳式"),
    ProductCategory.SEMI_IN_EAR: ("semi in ear", "semi-in-ear", "半入耳式"),
    ProductCategory.OVER_EAR: ("over ear", "over-ear", "头戴式", "包耳式"),
    ProductCategory.ON_EAR: ("on ear", "on-ear", "贴耳式"),
    ProductCategory.BONE_CONDUCTION: ("bone conduction", "骨传导"),
    ProductCategory.OPEN_EAR: ("open ear", "open-ear", "开放式"),
}


def build_lexical_text(product: NormalizedProduct) -> str:
    """Return a whitespace-delimited document suitable for PostgreSQL `simple` FTS."""

    parts = [
        product.brand,
        product.title,
        product.category.value,
        *_CATEGORY_ALIASES[product.category],
        f"{product.price_amount} {product.currency}",
        "headphones",
        "earphones",
        "耳机",
    ]
    if product.description:
        parts.append(product.description)
        parts.extend(term for term in _DESCRIPTION_TERMS if term in product.description)
    parts.extend(product.colors)
    parts.extend(product.codecs)
    if product.wireless is True:
        parts.extend(("wireless", "bluetooth", "无线"))
    elif product.wireless is False:
        parts.extend(("wired", "有线"))
    if product.anc is True:
        parts.extend(
            ("anc", "active noise cancelling", "active noise cancellation", "主动降噪", "降噪")
        )
    if product.battery_hours is not None:
        parts.extend((str(product.battery_hours), "hours", "battery", "续航", "小时"))
    if product.weight_grams is not None:
        parts.extend((str(product.weight_grams), "grams", "weight", "重量", "克"))
    if product.water_resistance:
        parts.extend((product.water_resistance, "water resistance", "防水"))
    if product.microphone:
        parts.extend((product.microphone, "microphone", "麦克风", "通话"))
    return "\n".join(parts)
