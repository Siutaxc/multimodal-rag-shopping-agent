"""Unit tests for the local content-addressed ObjectStorage adapter."""

from pathlib import Path

import pytest
from app.providers.storage import LocalObjectStorage


def test_local_storage_is_content_addressed_and_idempotent(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path / "objects")
    content = b"deterministic fixture image bytes"

    first = storage.put_bytes(content, "image/png")
    second = storage.put_bytes(content, "image/png")

    assert first == second
    assert first.byte_size == len(content)
    assert storage.resolve(first.key).read_bytes() == content
    assert len(list((tmp_path / "objects").rglob("*.png"))) == 1


@pytest.mark.parametrize(
    ("content", "media_type", "message"),
    [
        (b"", "image/png", "empty"),
        (b"content", "application/octet-stream", "unsupported media type"),
    ],
)
def test_local_storage_rejects_invalid_objects(
    tmp_path: Path, content: bytes, media_type: str, message: str
) -> None:
    storage = LocalObjectStorage(tmp_path)
    with pytest.raises(ValueError, match=message):
        storage.put_bytes(content, media_type)


def test_local_storage_rejects_path_traversal(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path / "objects")
    with pytest.raises(ValueError, match="escapes"):
        storage.resolve("../outside.png")
