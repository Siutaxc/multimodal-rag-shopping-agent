"""Idempotent and retryable batch materialization of versioned text embeddings."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Product, ProductDocument, TextEmbedding
from app.domain.products import DocumentType
from app.providers.retrieval import EmbeddingProvider, ProviderError
from app.retrieval.text_documents import DENSE_DOCUMENT_VERSION, build_dense_document


@dataclass(frozen=True)
class IndexingReport:
    total: int
    indexed: int
    skipped: int
    failed: int
    model_key: str
    document_version: str


class TextEmbeddingIndexer:
    """Persist only exact-version vectors and leave failed records retryable."""

    def __init__(self, session: Session, provider: EmbeddingProvider, *, batch_size: int) -> None:
        self._session = session
        self._provider = provider
        self._batch_size = batch_size

    def run(self) -> IndexingReport:
        total = int(
            self._session.scalar(
                select(func.count(ProductDocument.id)).where(
                    ProductDocument.document_type == DocumentType.MAIN
                )
            )
            or 0
        )
        indexed = skipped = failed = 0
        last_id = None
        while True:
            statement = (
                select(ProductDocument)
                .where(ProductDocument.document_type == DocumentType.MAIN)
                .options(
                    selectinload(ProductDocument.product).selectinload(Product.review_evidence)
                )
                .order_by(ProductDocument.id)
                .limit(self._batch_size)
            )
            if last_id is not None:
                statement = statement.where(ProductDocument.id > last_id)
            batch = list(self._session.scalars(statement).all())
            if not batch:
                break
            last_id = batch[-1].id
            pending: list[tuple[TextEmbedding, str]] = []
            for document in batch:
                text = build_dense_document(document.product)
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                record = self._find_record(document)
                if (
                    record is not None
                    and record.status == "ready"
                    and record.content_sha256 == digest
                ):
                    skipped += 1
                    continue
                if record is None:
                    identity = self._provider.identity
                    assert identity.dimension is not None
                    record = TextEmbedding(
                        document_id=document.id,
                        model_name=identity.model_name,
                        model_version=identity.model_version,
                        dimension=identity.dimension,
                        document_version=DENSE_DOCUMENT_VERSION,
                        source_document_version=document.document_version,
                        content_sha256=digest,
                        status="pending",
                    )
                    self._session.add(record)
                else:
                    record.source_document_version = document.document_version
                    record.content_sha256 = digest
                    record.status = "pending"
                    record.embedding = None
                    record.generated_at = None
                    record.last_error = None
                pending.append((record, text))
            self._session.commit()
            if not pending:
                continue
            try:
                vectors = self._provider.embed_texts([text for _, text in pending])
                if len(vectors) != len(pending):
                    raise ProviderError("embedding provider returned the wrong batch size")
                for (record, _), vector in zip(pending, vectors, strict=True):
                    record.embedding = vector
                    record.status = "ready"
                    record.generated_at = datetime.now(UTC)
                    record.last_error = None
                    indexed += 1
            except (ProviderError, ValueError) as error:
                message = str(error)[:1000]
                for record, _ in pending:
                    record.status = "failed"
                    record.embedding = None
                    record.last_error = message
                    failed += 1
            self._session.commit()
        return IndexingReport(
            total=total,
            indexed=indexed,
            skipped=skipped,
            failed=failed,
            model_key=self._provider.identity.version_key,
            document_version=DENSE_DOCUMENT_VERSION,
        )

    def _find_record(self, document: ProductDocument) -> TextEmbedding | None:
        identity = self._provider.identity
        assert identity.dimension is not None
        return self._session.scalar(
            select(TextEmbedding).where(
                TextEmbedding.document_id == document.id,
                TextEmbedding.model_name == identity.model_name,
                TextEmbedding.model_version == identity.model_version,
                TextEmbedding.dimension == identity.dimension,
                TextEmbedding.document_version == DENSE_DOCUMENT_VERSION,
            )
        )
