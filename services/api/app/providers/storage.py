"""Content-addressed local object storage for stage-two product assets."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class StoredObject:
    """Immutable metadata returned after a local object is persisted."""

    key: str
    sha256: str
    byte_size: int
    media_type: str


class ObjectStorage(Protocol):
    """Minimal storage boundary that can later be implemented by S3-compatible storage."""

    def put_bytes(self, content: bytes, media_type: str) -> StoredObject:
        """Persist non-empty bytes and return a content-addressed reference."""

    def put_file(self, source: Path, media_type: str) -> StoredObject:
        """Persist a local source file."""

    def resolve(self, key: str) -> Path:
        """Resolve a provider-owned key without permitting path traversal."""


_MEDIA_SUFFIXES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}


class LocalObjectStorage:
    """Atomic content-addressed storage rooted in a configured local directory."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, content: bytes, media_type: str) -> StoredObject:
        if not content:
            raise ValueError("cannot store an empty object")
        suffix = _MEDIA_SUFFIXES.get(media_type)
        if suffix is None:
            raise ValueError(f"unsupported media type: {media_type}")

        digest = hashlib.sha256(content).hexdigest()
        key = f"images/{digest[:2]}/{digest[2:4]}/{digest}{suffix}"
        target = self.resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
            try:
                temporary.write_bytes(content)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        return StoredObject(
            key=key,
            sha256=digest,
            byte_size=len(content),
            media_type=media_type,
        )

    def put_file(self, source: Path, media_type: str) -> StoredObject:
        if not source.is_file():
            raise ValueError(f"asset file does not exist: {source}")
        return self.put_bytes(source.read_bytes(), media_type)

    def resolve(self, key: str) -> Path:
        if not key or Path(key).is_absolute():
            raise ValueError("storage key must be a non-empty relative path")
        resolved = (self._root / key).resolve()
        if not resolved.is_relative_to(self._root):
            raise ValueError("storage key escapes the configured root")
        return resolved
