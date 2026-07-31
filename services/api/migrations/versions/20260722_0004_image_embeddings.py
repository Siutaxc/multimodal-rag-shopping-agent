"""Add sanitized upload assets and versioned SigLIP2 image embeddings.

Revision ID: 20260722_0004
Revises: 20260722_0003
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "20260722_0004"
down_revision: str | None = "20260722_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create an independent image vector index and sanitized upload registry."""

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "uploaded_image_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("original_sha256", sa.String(length=64), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "byte_size > 0",
            name="ck_uploaded_image_assets_uploaded_image_byte_size_positive",
        ),
        sa.CheckConstraint(
            "width > 0", name="ck_uploaded_image_assets_uploaded_image_width_positive"
        ),
        sa.CheckConstraint(
            "height > 0", name="ck_uploaded_image_assets_uploaded_image_height_positive"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_uploaded_image_assets"),
        sa.UniqueConstraint("storage_key", name="uq_uploaded_image_assets_storage_key"),
    )
    op.create_index(
        "ix_uploaded_image_assets_content_sha256", "uploaded_image_assets", ["content_sha256"]
    )
    op.create_table(
        "image_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("image_id", sa.Uuid(), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("representation_version", sa.String(length=120), nullable=False),
        sa.Column("source_image_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("dimension = 768", name="ck_image_embeddings_dimension_siglip2_base"),
        sa.CheckConstraint(
            "status IN ('pending', 'ready', 'failed')",
            name="ck_image_embeddings_image_embedding_status_known",
        ),
        sa.ForeignKeyConstraint(
            ["image_id"],
            ["product_images.id"],
            name="fk_image_embeddings_image_id_product_images",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_image_embeddings"),
        sa.UniqueConstraint(
            "image_id",
            "model_name",
            "model_version",
            "dimension",
            "representation_version",
            name="uq_image_embeddings_version",
        ),
    )
    op.create_index(
        "ix_image_embeddings_active_version",
        "image_embeddings",
        ["model_name", "model_version", "dimension", "representation_version", "status"],
    )
    op.create_index(
        "ix_image_embeddings_hnsw_cosine",
        "image_embeddings",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_where=sa.text("status = 'ready'"),
    )


def downgrade() -> None:
    """Remove stage-five assets while retaining product image metadata."""

    op.drop_index("ix_image_embeddings_hnsw_cosine", table_name="image_embeddings")
    op.drop_index("ix_image_embeddings_active_version", table_name="image_embeddings")
    op.drop_table("image_embeddings")
    op.drop_index("ix_uploaded_image_assets_content_sha256", table_name="uploaded_image_assets")
    op.drop_table("uploaded_image_assets")
