"""Decode, validate, orient, and metadata-strip untrusted uploaded raster images."""

import hashlib
import io
import warnings
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError


class ImageValidationError(ValueError):
    """An upload violates a documented image safety limit."""


@dataclass(frozen=True)
class SanitizedImage:
    """Canonical lossless WebP bytes and auditable source metadata."""

    content: bytes
    media_type: str
    width: int
    height: int
    original_sha256: str
    content_sha256: str


ALLOWED_IMAGE_TYPES = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}


def sanitize_image(
    content: bytes,
    declared_media_type: str,
    *,
    max_bytes: int,
    max_pixels: int,
    max_dimension: int,
) -> SanitizedImage:
    """Reject disguised/animated/bomb-like inputs and retain only decoded pixels."""

    media_type = declared_media_type.split(";", 1)[0].strip().casefold()
    if media_type not in ALLOWED_IMAGE_TYPES:
        raise ImageValidationError("supported image types are JPEG, PNG, and WebP")
    if not content:
        raise ImageValidationError("image body is empty")
    if len(content) > max_bytes:
        raise ImageValidationError("image exceeds the configured byte limit")

    original_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = max_pixels
    try:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as probe:
                    if probe.format != ALLOWED_IMAGE_TYPES[media_type]:
                        raise ImageValidationError(
                            "declared media type does not match decoded image"
                        )
                    if getattr(probe, "is_animated", False) or getattr(probe, "n_frames", 1) != 1:
                        raise ImageValidationError("animated images are not supported")
                    width, height = probe.size
                    if width * height > max_pixels:
                        raise ImageValidationError("image exceeds the configured pixel limit")
                    if max(width, height) > max_dimension:
                        raise ImageValidationError("image exceeds the configured dimension limit")
                    probe.verify()
            with Image.open(io.BytesIO(content)) as decoded:
                pixels = ImageOps.exif_transpose(decoded).convert("RGB")
                pixels.load()
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
            raise ImageValidationError("image exceeds the configured pixel limit") from error
        except UnidentifiedImageError as error:
            raise ImageValidationError("body is not a decodable supported image") from error
        except OSError as error:
            raise ImageValidationError("image data is truncated or invalid") from error
    finally:
        Image.MAX_IMAGE_PIXELS = original_limit

    output = io.BytesIO()
    pixels.save(output, format="WEBP", lossless=True, method=6, exif=b"")
    sanitized = output.getvalue()
    return SanitizedImage(
        content=sanitized,
        media_type="image/webp",
        width=pixels.width,
        height=pixels.height,
        original_sha256=hashlib.sha256(content).hexdigest(),
        content_sha256=hashlib.sha256(sanitized).hexdigest(),
    )
