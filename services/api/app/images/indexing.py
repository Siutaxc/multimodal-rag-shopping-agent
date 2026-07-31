"""Idempotent batch materialization of versioned product image embeddings."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ImageEmbedding, ProductImage
from app.providers.images import ImageEmbeddingProvider
from app.providers.retrieval import ProviderError
from app.providers.storage import ObjectStorage

IMAGE_REPRESENTATION_VERSION = "stage5-product-image-v1"


@dataclass(frozen=True)
class ImageIndexingReport:
    total: int
    indexed: int
    skipped: int
    failed: int
    model_key: str
    representation_version: str


class ImageEmbeddingIndexer:
    """Persist exact-version image vectors and keep failed records retryable."""

    def __init__(
        self,
        session: Session,
        provider: ImageEmbeddingProvider,
        storage: ObjectStorage,
        *,
        batch_size: int,
    ) -> None:
        self._session = session
        self._provider = provider
        self._storage = storage
        self._batch_size = batch_size

    def run(self) -> ImageIndexingReport:
        total = int(self._session.scalar(select(func.count(ProductImage.id))) or 0)
        indexed = skipped = failed = 0
        last_id = None
        while True:
            statement = select(ProductImage).order_by(ProductImage.id).limit(self._batch_size)
            if last_id is not None:
                statement = statement.where(ProductImage.id > last_id)
            batch = list(self._session.scalars(statement).all())
            if not batch:
                break
            last_id = batch[-1].id
            pending: list[tuple[ImageEmbedding, bytes]] = []
            for image in batch:
                record = self._find_record(image)
                if (
                    record is not None
                    and record.status == "ready"
                    and record.source_image_sha256 == image.sha256
                ):
                    skipped += 1
                    continue
                if record is None:
                    identity = self._provider.identity
                    assert identity.dimension is not None
                    record = ImageEmbedding(
                        image_id=image.id,
                        model_name=identity.model_name,
                        model_version=identity.model_version,
                        dimension=identity.dimension,
                        representation_version=IMAGE_REPRESENTATION_VERSION,
                        source_image_sha256=image.sha256,
                        status="pending",
                    )
                    self._session.add(record)
                else:
                    record.source_image_sha256 = image.sha256
                    record.status = "pending"
                    record.embedding = None
                    record.generated_at = None
                    record.last_error = None
                try:
                    content = self._storage.resolve(image.storage_key).read_bytes()
                    pending.append((record, content))
                except (OSError, ValueError) as error:
                    record.status = "failed"
                    record.last_error = str(error)[:1000]
                    failed += 1
            self._session.commit()
            if not pending:
                continue
            try:
                vectors = self._provider.embed_images([content for _, content in pending])
                if len(vectors) != len(pending):
                    raise ProviderError("image provider returned the wrong batch size")
                for (record, _), vector in zip(pending, vectors, strict=True):
                    record.embedding = vector
                    record.status = "ready"
                    record.generated_at = datetime.now(UTC)
                    record.last_error = None
                    indexed += 1
            except (ProviderError, ValueError) as error:
                for record, _ in pending:
                    record.status = "failed"
                    record.embedding = None
                    record.last_error = str(error)[:1000]
                    failed += 1
            self._session.commit()
        return ImageIndexingReport(
            total=total,
            indexed=indexed,
            skipped=skipped,
            failed=failed,
            model_key=self._provider.identity.version_key,
            representation_version=IMAGE_REPRESENTATION_VERSION,
        )

    def _find_record(self, image: ProductImage) -> ImageEmbedding | None:
        identity = self._provider.identity
        assert identity.dimension is not None
        return self._session.scalar(
            select(ImageEmbedding).where(
                ImageEmbedding.image_id == image.id,
                ImageEmbedding.model_name == identity.model_name,
                ImageEmbedding.model_version == identity.model_version,
                ImageEmbedding.dimension == identity.dimension,
                ImageEmbedding.representation_version == IMAGE_REPRESENTATION_VERSION,
            )
        )
