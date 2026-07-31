"""Versioned fact and evidence text for dense retrieval and reranking."""

from app.db.models import Product

DENSE_DOCUMENT_VERSION = "stage4-dense-v1"


def build_dense_document(product: Product) -> str:
    """Join persisted facts and review evidence without inventing new claims."""

    lines = [
        f"品牌: {product.brand}",
        f"商品: {product.title}",
        f"类型: {product.category.value}",
        f"价格: {product.price_amount} {product.currency}",
    ]
    if product.description:
        lines.append(f"描述: {product.description}")
    if product.wireless is not None:
        lines.append(f"连接: {'无线' if product.wireless else '有线'}")
    if product.anc is not None:
        lines.append(f"主动降噪: {'支持' if product.anc else '不支持'}")
    if product.battery_hours is not None:
        lines.append(f"续航: {product.battery_hours} 小时")
    if product.weight_grams is not None:
        lines.append(f"重量: {product.weight_grams} 克")
    if product.colors:
        lines.append(f"颜色: {'、'.join(product.colors)}")
    if product.codecs:
        lines.append(f"编码: {'、'.join(product.codecs)}")
    if product.water_resistance:
        lines.append(f"防水: {product.water_resistance}")
    if product.microphone:
        lines.append(f"麦克风: {product.microphone}")
    lines.extend(
        f"评论证据[{evidence.topic.value}]: {evidence.excerpt}"
        for evidence in sorted(product.review_evidence, key=lambda item: str(item.id))
    )
    return "\n".join(lines)
