"""Add covering indexes for stage-eight filtered retrieval at scale.

Revision ID: 20260722_0005
Revises: 20260722_0004
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0005"
down_revision: str | None = "20260722_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Support common hard-filter prefixes and exact active-vector joins."""

    op.create_index(
        "ix_products_search_hard_filters",
        "products",
        ["category", "currency", "anc", "wireless", "price_amount", "id"],
    )
    op.create_index(
        "ix_text_embeddings_ready_version_document",
        "text_embeddings",
        ["model_name", "model_version", "dimension", "document_version", "document_id"],
        postgresql_where=sa.text("status = 'ready' AND embedding IS NOT NULL"),
    )
    op.create_index(
        "ix_image_embeddings_ready_version_image",
        "image_embeddings",
        [
            "model_name",
            "model_version",
            "dimension",
            "representation_version",
            "image_id",
        ],
        postgresql_where=sa.text("status = 'ready' AND embedding IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_image_embeddings_ready_version_image", table_name="image_embeddings")
    op.drop_index("ix_text_embeddings_ready_version_document", table_name="text_embeddings")
    op.drop_index("ix_products_search_hard_filters", table_name="products")
