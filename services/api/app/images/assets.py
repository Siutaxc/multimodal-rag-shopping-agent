"""Application service for sanitized, content-addressed uploaded image assets."""

from sqlalchemy.exc import IntegrityError

from app.db.images import UploadedImageAssetRepository
from app.db.models import UploadedImageAsset
from app.images.processing import SanitizedImage
from app.providers.storage import ObjectStorage


class ImageAssetService:
    """Store sanitized pixels and return a stable opaque database identifier."""

    def __init__(self, repository: UploadedImageAssetRepository, storage: ObjectStorage) -> None:
        self._repository = repository
        self._storage = storage

    def persist(self, image: SanitizedImage) -> UploadedImageAsset:
        existing = self._repository.find_by_content_sha256(image.content_sha256)
        if existing is not None:
            return existing
        stored = self._storage.put_bytes(image.content, image.media_type)
        asset = UploadedImageAsset(
            storage_key=stored.key,
            original_sha256=image.original_sha256,
            content_sha256=image.content_sha256,
            media_type=stored.media_type,
            byte_size=stored.byte_size,
            width=image.width,
            height=image.height,
        )
        try:
            return self._repository.add(asset)
        except IntegrityError:
            existing = self._repository.find_by_content_sha256(image.content_sha256)
            if existing is None:
                raise
            return existing
