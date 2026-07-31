"""Stage-two relational product and ingestion models."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.domain.products import DocumentType, IngestionStatus, ProductCategory, ReviewTopic


class Product(TimestampMixin, Base):
    """Canonical product facts; unknown structured values remain null."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("source_name", "source_id", name="uq_products_source_identity"),
        UniqueConstraint("idempotency_key", name="uq_products_idempotency_key"),
        UniqueConstraint("dedupe_key", name="uq_products_dedupe_key"),
        CheckConstraint("price_amount >= 0", name="price_amount_non_negative"),
        CheckConstraint("char_length(currency) = 3", name="currency_iso_length"),
        CheckConstraint(
            "battery_hours IS NULL OR battery_hours > 0", name="battery_hours_positive"
        ),
        CheckConstraint("weight_grams IS NULL OR weight_grams > 0", name="weight_grams_positive"),
        Index("ix_products_currency_price", "currency", "price_amount"),
        Index("ix_products_category_price", "category", "price_amount"),
        Index("ix_products_brand", "brand"),
        Index("ix_products_anc", "anc"),
        Index("ix_products_wireless", "wireless"),
        Index("ix_products_battery_hours", "battery_hours"),
        Index(
            "ix_products_search_hard_filters",
            "category",
            "currency",
            "anc",
            "wireless",
            "price_amount",
            "id",
        ),
        Index("ix_products_colors_gin", "colors", postgresql_using="gin"),
        Index("ix_products_codecs_gin", "codecs", postgresql_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_version: Mapped[str] = mapped_column(String(120), nullable=False)
    transformation_version: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[ProductCategory] = mapped_column(
        Enum(
            ProductCategory,
            name="product_category",
            native_enum=False,
            create_constraint=True,
            length=32,
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    price_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    wireless: Mapped[bool | None] = mapped_column(Boolean)
    anc: Mapped[bool | None] = mapped_column(Boolean)
    battery_hours: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    weight_grams: Mapped[Decimal | None] = mapped_column(Numeric(9, 2))
    colors: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    codecs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    water_resistance: Mapped[str | None] = mapped_column(String(32))
    microphone: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.position"
    )
    documents: Mapped[list["ProductDocument"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    review_evidence: Mapped[list["ReviewEvidence"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductImage(TimestampMixin, Base):
    """Locally stored product image metadata; bytes live behind ObjectStorage."""

    __tablename__ = "product_images"
    __table_args__ = (
        UniqueConstraint("sha256", name="uq_product_images_sha256"),
        UniqueConstraint("product_id", "position", name="uq_product_images_position"),
        CheckConstraint("position >= 0", name="position_non_negative"),
        CheckConstraint("byte_size > 0", name="byte_size_positive"),
        CheckConstraint("width IS NULL OR width > 0", name="width_positive"),
        CheckConstraint("height IS NULL OR height > 0", name="height_positive"),
        Index("ix_product_images_product_id", "product_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    alt_text: Mapped[str | None] = mapped_column(String(500))

    product: Mapped[Product] = relationship(back_populates="images")
    embeddings: Mapped[list["ImageEmbedding"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )


class ImageEmbedding(TimestampMixin, Base):
    """Auditable SigLIP2 image vectors selected by an exact source/model tuple."""

    __tablename__ = "image_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "image_id",
            "model_name",
            "model_version",
            "dimension",
            "representation_version",
            name="uq_image_embeddings_version",
        ),
        CheckConstraint("dimension = 768", name="dimension_siglip2_base"),
        CheckConstraint(
            "status IN ('pending', 'ready', 'failed')", name="image_embedding_status_known"
        ),
        Index(
            "ix_image_embeddings_active_version",
            "model_name",
            "model_version",
            "dimension",
            "representation_version",
            "status",
        ),
        Index(
            "ix_image_embeddings_hnsw_cosine",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_where=text("status = 'ready'"),
        ),
        Index(
            "ix_image_embeddings_ready_version_image",
            "model_name",
            "model_version",
            "dimension",
            "representation_version",
            "image_id",
            postgresql_where=text("status = 'ready' AND embedding IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    image_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_images.id", ondelete="CASCADE"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    representation_version: Mapped[str] = mapped_column(String(120), nullable=False)
    source_image_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    image: Mapped[ProductImage] = relationship(back_populates="embeddings")


class UploadedImageAsset(TimestampMixin, Base):
    """Sanitized user-uploaded image metadata; raw user bytes are never retained."""

    __tablename__ = "uploaded_image_assets"
    __table_args__ = (
        CheckConstraint("byte_size > 0", name="uploaded_image_byte_size_positive"),
        CheckConstraint("width > 0", name="uploaded_image_width_positive"),
        CheckConstraint("height > 0", name="uploaded_image_height_positive"),
        UniqueConstraint("storage_key", name="uq_uploaded_image_assets_storage_key"),
        Index("ix_uploaded_image_assets_content_sha256", "content_sha256"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)


class ProductDocument(TimestampMixin, Base):
    """Versioned source and lexical text used by deterministic retrieval."""

    __tablename__ = "product_documents"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "document_type", "document_version", name="uq_product_documents_version"
        ),
        Index("ix_product_documents_product_id", "product_id"),
        Index("ix_product_documents_search_vector_gin", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(
            DocumentType,
            name="document_type",
            native_enum=False,
            create_constraint=True,
            length=32,
        ),
        nullable=False,
    )
    document_version: Mapped[str] = mapped_column(String(120), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="zh-CN")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple'::regconfig, search_text)", persisted=True),
    )

    product: Mapped[Product] = relationship(back_populates="documents")
    embeddings: Mapped[list["TextEmbedding"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class TextEmbedding(TimestampMixin, Base):
    """Auditable BGE-M3 text vectors selected by an exact version tuple."""

    __tablename__ = "text_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "model_name",
            "model_version",
            "dimension",
            "document_version",
            name="uq_text_embeddings_version",
        ),
        CheckConstraint("dimension = 1024", name="dimension_bge_m3"),
        CheckConstraint("status IN ('pending', 'ready', 'failed')", name="status_known"),
        Index(
            "ix_text_embeddings_active_version",
            "model_name",
            "model_version",
            "dimension",
            "document_version",
            "status",
        ),
        Index(
            "ix_text_embeddings_hnsw_cosine",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_where=text("status = 'ready'"),
        ),
        Index(
            "ix_text_embeddings_ready_version_document",
            "model_name",
            "model_version",
            "dimension",
            "document_version",
            "document_id",
            postgresql_where=text("status = 'ready' AND embedding IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_documents.id", ondelete="CASCADE"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    document_version: Mapped[str] = mapped_column(String(120), nullable=False)
    source_document_version: Mapped[str] = mapped_column(String(120), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    document: Mapped[ProductDocument] = relationship(back_populates="embeddings")


class ReviewEvidence(TimestampMixin, Base):
    """Quoted review evidence with its original external identity."""

    __tablename__ = "review_evidence"
    __table_args__ = (
        UniqueConstraint(
            "source_name", "source_review_id", "topic", name="uq_review_evidence_source_topic"
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 0 AND rating <= 5)", name="rating_valid_range"
        ),
        Index("ix_review_evidence_product_topic", "product_id", "topic"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_review_id: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[ReviewTopic] = mapped_column(
        Enum(
            ReviewTopic,
            name="review_topic",
            native_enum=False,
            create_constraint=True,
            length=32,
        ),
        nullable=False,
    )
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str | None] = mapped_column(String(2048))

    product: Mapped[Product] = relationship(back_populates="review_evidence")


class IngestionJob(Base):
    """Auditable counters and errors for every ingestion attempt."""

    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        CheckConstraint("total_count >= 0", name="total_count_non_negative"),
        CheckConstraint("succeeded_count >= 0", name="succeeded_count_non_negative"),
        CheckConstraint("failed_count >= 0", name="failed_count_non_negative"),
        CheckConstraint("skipped_count >= 0", name="skipped_count_non_negative"),
        Index("ix_ingestion_jobs_batch_key", "batch_key"),
        Index("ix_ingestion_jobs_status_started", "status", "started_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    batch_key: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_version: Mapped[str] = mapped_column(String(120), nullable=False)
    transformation_version: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(
            IngestionStatus,
            name="ingestion_status",
            native_enum=False,
            create_constraint=True,
            length=32,
        ),
        nullable=False,
    )
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    succeeded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
