"""Untrusted upload decoding, type matching, limits, and metadata stripping."""

import io

import pytest
from app.images.processing import ImageValidationError, sanitize_image
from PIL import Image, PngImagePlugin


def _png(*, width: int = 32, height: int = 24, metadata: bool = False) -> bytes:
    output = io.BytesIO()
    info = None
    if metadata:
        info = PngImagePlugin.PngInfo()
        info.add_text("private-note", "must not survive")
    Image.new("RGB", (width, height), "#345678").save(output, format="PNG", pnginfo=info)
    return output.getvalue()


def test_sanitize_image_reencodes_lossless_webp_and_strips_metadata() -> None:
    original = _png(metadata=True)

    result = sanitize_image(
        original,
        "image/png",
        max_bytes=100_000,
        max_pixels=1_000_000,
        max_dimension=1024,
    )

    assert result.media_type == "image/webp"
    assert (result.width, result.height) == (32, 24)
    assert result.original_sha256 != result.content_sha256
    with Image.open(io.BytesIO(result.content)) as decoded:
        assert decoded.format == "WEBP"
        assert "private-note" not in decoded.info


@pytest.mark.parametrize(
    ("body", "media_type", "message"),
    [
        (_png(), "image/jpeg", "does not match"),
        (b"not an image", "image/png", "not a decodable"),
        (_png(), "image/svg+xml", "supported image types"),
    ],
)
def test_sanitize_image_rejects_disguised_or_unsupported_inputs(
    body: bytes, media_type: str, message: str
) -> None:
    with pytest.raises(ImageValidationError, match=message):
        sanitize_image(
            body,
            media_type,
            max_bytes=100_000,
            max_pixels=1_000_000,
            max_dimension=1024,
        )


def test_sanitize_image_enforces_byte_pixel_and_dimension_limits() -> None:
    body = _png(width=40, height=30)
    with pytest.raises(ImageValidationError, match="byte limit"):
        sanitize_image(
            body,
            "image/png",
            max_bytes=len(body) - 1,
            max_pixels=10_000,
            max_dimension=100,
        )
    with pytest.raises(ImageValidationError, match="pixel limit"):
        sanitize_image(
            body,
            "image/png",
            max_bytes=100_000,
            max_pixels=1_000,
            max_dimension=100,
        )
    with pytest.raises(ImageValidationError, match="dimension limit"):
        sanitize_image(
            body,
            "image/png",
            max_bytes=100_000,
            max_pixels=10_000,
            max_dimension=32,
        )
