"""Add versioned BGE-M3 text embeddings and a cosine HNSW index.

Revision ID: 20260722_0003
Revises: 20260722_0002
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "20260722_0003"
down_revision: str | None = "20260722_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create an auditable vector record per exact provider/document version."""

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "text_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("document_version", sa.String(length=120), nullable=False),
        sa.Column("source_document_version", sa.String(length=120), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=True),
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
        sa.CheckConstraint("dimension = 1024", name="ck_text_embeddings_dimension_bge_m3"),
        sa.CheckConstraint(
            "status IN ('pending', 'ready', 'failed')",
            name="ck_text_embeddings_status_known",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["product_documents.id"],
            name="fk_text_embeddings_document_id_product_documents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_text_embeddings"),
        sa.UniqueConstraint(
            "document_id",
            "model_name",
            "model_version",
            "dimension",
            "document_version",
            name="uq_text_embeddings_version",
        ),
    )
    op.create_index(
        "ix_text_embeddings_active_version",
        "text_embeddings",
        ["model_name", "model_version", "dimension", "document_version", "status"],
    )
    op.create_index(
        "ix_text_embeddings_hnsw_cosine",
        "text_embeddings",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_where=sa.text("status = 'ready'"),
    )


def downgrade() -> None:
    """Remove text vectors while leaving the shared pgvector extension installed."""

    op.drop_index("ix_text_embeddings_hnsw_cosine", table_name="text_embeddings")
    op.drop_index("ix_text_embeddings_active_version", table_name="text_embeddings")
    op.drop_table("text_embeddings")
