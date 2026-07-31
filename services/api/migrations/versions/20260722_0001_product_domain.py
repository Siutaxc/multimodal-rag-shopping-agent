"""Create the deterministic product and ingestion domain.

Revision ID: 20260722_0001
Revises: None
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260722_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create stage-two tables, constraints, and structured-filter indexes."""

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("source_version", sa.String(length=120), nullable=False),
        sa.Column("transformation_version", sa.String(length=120), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("dedupe_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("brand", sa.String(length=160), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "IN_EAR",
                "SEMI_IN_EAR",
                "OVER_EAR",
                "ON_EAR",
                "BONE_CONDUCTION",
                "OPEN_EAR",
                name="product_category",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("price_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("wireless", sa.Boolean(), nullable=True),
        sa.Column("anc", sa.Boolean(), nullable=True),
        sa.Column("battery_hours", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("weight_grams", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("colors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("codecs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("water_resistance", sa.String(length=32), nullable=True),
        sa.Column("microphone", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
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
            "battery_hours IS NULL OR battery_hours > 0", name="ck_products_battery_hours_positive"
        ),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_products_currency_iso_length"),
        sa.CheckConstraint("price_amount >= 0", name="ck_products_price_amount_non_negative"),
        sa.CheckConstraint(
            "weight_grams IS NULL OR weight_grams > 0", name="ck_products_weight_grams_positive"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.UniqueConstraint("dedupe_key", name="uq_products_dedupe_key"),
        sa.UniqueConstraint("idempotency_key", name="uq_products_idempotency_key"),
        sa.UniqueConstraint("source_name", "source_id", name="uq_products_source_identity"),
    )
    op.create_index("ix_products_anc", "products", ["anc"])
    op.create_index("ix_products_battery_hours", "products", ["battery_hours"])
    op.create_index("ix_products_brand", "products", ["brand"])
    op.create_index("ix_products_category_price", "products", ["category", "price_amount"])
    op.create_index("ix_products_codecs_gin", "products", ["codecs"], postgresql_using="gin")
    op.create_index("ix_products_colors_gin", "products", ["colors"], postgresql_using="gin")
    op.create_index("ix_products_currency_price", "products", ["currency", "price_amount"])
    op.create_index("ix_products_wireless", "products", ["wireless"])

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_key", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_version", sa.String(length=120), nullable=False),
        sa.Column("transformation_version", sa.String(length=120), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "RUNNING",
                "SUCCESS",
                "PARTIAL",
                "FAILED",
                name="ingestion_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("succeeded_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("errors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("failed_count >= 0", name="ck_ingestion_jobs_failed_count_non_negative"),
        sa.CheckConstraint(
            "skipped_count >= 0", name="ck_ingestion_jobs_skipped_count_non_negative"
        ),
        sa.CheckConstraint(
            "succeeded_count >= 0", name="ck_ingestion_jobs_succeeded_count_non_negative"
        ),
        sa.CheckConstraint("total_count >= 0", name="ck_ingestion_jobs_total_count_non_negative"),
        sa.PrimaryKeyConstraint("id", name="pk_ingestion_jobs"),
    )
    op.create_index("ix_ingestion_jobs_batch_key", "ingestion_jobs", ["batch_key"])
    op.create_index("ix_ingestion_jobs_status_started", "ingestion_jobs", ["status", "started_at"])

    op.create_table(
        "product_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column(
            "document_type",
            sa.Enum(
                "MAIN",
                name="document_type",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("document_version", sa.String(length=120), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_documents_product_id_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_product_documents"),
        sa.UniqueConstraint(
            "product_id", "document_type", "document_version", name="uq_product_documents_version"
        ),
    )
    op.create_index("ix_product_documents_product_id", "product_documents", ["product_id"])

    op.create_table(
        "product_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("alt_text", sa.String(length=500), nullable=True),
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
        sa.CheckConstraint("byte_size > 0", name="ck_product_images_byte_size_positive"),
        sa.CheckConstraint(
            "height IS NULL OR height > 0", name="ck_product_images_height_positive"
        ),
        sa.CheckConstraint("position >= 0", name="ck_product_images_position_non_negative"),
        sa.CheckConstraint("width IS NULL OR width > 0", name="ck_product_images_width_positive"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_images_product_id_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_product_images"),
        sa.UniqueConstraint("product_id", "position", name="uq_product_images_position"),
        sa.UniqueConstraint("sha256", name="uq_product_images_sha256"),
    )
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])

    op.create_table(
        "review_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_review_id", sa.String(length=255), nullable=False),
        sa.Column(
            "topic",
            sa.Enum(
                "ANC",
                "COMFORT",
                "SOUND",
                "MICROPHONE",
                "BATTERY",
                "OTHER",
                name="review_topic",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("rating", sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
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
            "rating IS NULL OR (rating >= 0 AND rating <= 5)",
            name="ck_review_evidence_rating_valid_range",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_review_evidence_product_id_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_review_evidence"),
        sa.UniqueConstraint(
            "source_name", "source_review_id", "topic", name="uq_review_evidence_source_topic"
        ),
    )
    op.create_index("ix_review_evidence_product_topic", "review_evidence", ["product_id", "topic"])


def downgrade() -> None:
    """Remove stage-two schema objects in reverse dependency order."""

    op.drop_index("ix_review_evidence_product_topic", table_name="review_evidence")
    op.drop_table("review_evidence")
    op.drop_index("ix_product_images_product_id", table_name="product_images")
    op.drop_table("product_images")
    op.drop_index("ix_product_documents_product_id", table_name="product_documents")
    op.drop_table("product_documents")
    op.drop_index("ix_ingestion_jobs_status_started", table_name="ingestion_jobs")
    op.drop_index("ix_ingestion_jobs_batch_key", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    op.drop_index("ix_products_wireless", table_name="products")
    op.drop_index("ix_products_currency_price", table_name="products")
    op.drop_index("ix_products_colors_gin", table_name="products", postgresql_using="gin")
    op.drop_index("ix_products_codecs_gin", table_name="products", postgresql_using="gin")
    op.drop_index("ix_products_category_price", table_name="products")
    op.drop_index("ix_products_brand", table_name="products")
    op.drop_index("ix_products_battery_hours", table_name="products")
    op.drop_index("ix_products_anc", table_name="products")
    op.drop_table("products")
