"""Add the stage-three PostgreSQL lexical search document and GIN index.

Revision ID: 20260722_0002
Revises: 20260722_0001
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260722_0002"
down_revision: str | None = "20260722_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Backfill a fact-only search document, then add a stored tsvector and GIN index."""

    op.add_column("product_documents", sa.Column("search_text", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE product_documents AS document
            SET search_text = concat_ws(
                E'\n',
                product.brand,
                product.title,
                product.category,
                CASE product.category
                    WHEN 'IN_EAR' THEN 'in ear in-ear 入耳式'
                    WHEN 'SEMI_IN_EAR' THEN 'semi in ear semi-in-ear 半入耳式'
                    WHEN 'OVER_EAR' THEN 'over ear over-ear 头戴式 包耳式'
                    WHEN 'ON_EAR' THEN 'on ear on-ear 贴耳式'
                    WHEN 'BONE_CONDUCTION' THEN 'bone conduction 骨传导'
                    WHEN 'OPEN_EAR' THEN 'open ear open-ear 开放式'
                END,
                concat(product.price_amount, ' ', product.currency),
                'headphones earphones 耳机',
                product.description,
                CASE WHEN product.description LIKE '%通勤%' THEN '通勤' END,
                CASE WHEN product.description LIKE '%办公%' THEN '办公' END,
                CASE WHEN product.description LIKE '%户外%' THEN '户外' END,
                CASE WHEN product.description LIKE '%运动%' THEN '运动' END,
                CASE WHEN product.description LIKE '%游泳%' THEN '游泳' END,
                CASE WHEN product.description LIKE '%室内%' THEN '室内' END,
                CASE WHEN product.description LIKE '%便携%' THEN '便携' END,
                CASE WHEN product.description LIKE '%旅行%' THEN '旅行' END,
                CASE WHEN product.description LIKE '%长续航%' THEN '长续航' END,
                CASE WHEN product.description LIKE '%轻量%' THEN '轻量' END,
                CASE WHEN product.description LIKE '%可折叠%' THEN '可折叠' END,
                CASE WHEN product.description LIKE '%耳夹%' THEN '耳夹' END,
                CASE WHEN product.description LIKE '%充电盒%' THEN '充电盒' END,
                product.colors::text,
                product.codecs::text,
                CASE WHEN product.wireless IS TRUE THEN 'wireless bluetooth 无线'
                     WHEN product.wireless IS FALSE THEN 'wired 有线' END,
                CASE WHEN product.anc IS TRUE
                     THEN 'anc active noise cancelling active noise cancellation 主动降噪 降噪' END,
                CASE WHEN product.battery_hours IS NOT NULL
                     THEN concat(product.battery_hours, ' hours battery 续航 小时') END,
                CASE WHEN product.weight_grams IS NOT NULL
                     THEN concat(product.weight_grams, ' grams weight 重量 克') END,
                CASE WHEN product.water_resistance IS NOT NULL
                     THEN concat(product.water_resistance, ' water resistance 防水') END,
                CASE WHEN product.microphone IS NOT NULL
                     THEN concat(product.microphone, ' microphone 麦克风 通话') END
            )
            FROM products AS product
            WHERE product.id = document.product_id
            """
        )
    )
    op.alter_column("product_documents", "search_text", existing_type=sa.Text(), nullable=False)
    op.add_column(
        "product_documents",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple'::regconfig, search_text)", persisted=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_product_documents_search_vector_gin",
        "product_documents",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Remove stage-three lexical search state while preserving source documents."""

    op.drop_index("ix_product_documents_search_vector_gin", table_name="product_documents")
    op.drop_column("product_documents", "search_vector")
    op.drop_column("product_documents", "search_text")
