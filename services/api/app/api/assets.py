"""Raw-body HTTP image upload endpoint with streaming byte limits and sanitization."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.settings import Settings, get_settings
from app.db.images import UploadedImageAssetRepository
from app.db.session import get_db_session
from app.images.assets import ImageAssetService
from app.images.processing import ImageValidationError, sanitize_image
from app.providers.storage import LocalObjectStorage

router = APIRouter(prefix="/assets", tags=["assets"])


class UploadedImageResponse(BaseModel):
    asset_id: UUID
    media_type: str
    byte_size: int
    width: int
    height: int
    content_sha256: str


async def _bounded_body(request: Request, max_bytes: int) -> bytes:
    declared_length = request.headers.get("content-length")
    if declared_length is not None:
        try:
            if int(declared_length) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="image exceeds the configured byte limit",
                )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="invalid Content-Length"
            ) from error
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="image exceeds the configured byte limit",
            )
    return bytes(body)


@router.post("/images", response_model=UploadedImageResponse, status_code=201)
async def upload_image(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadedImageResponse:
    """Accept one raster image as the request body; multipart is intentionally unnecessary."""

    content = await _bounded_body(request, settings.image_upload_max_bytes)
    try:
        sanitized = sanitize_image(
            content,
            request.headers.get("content-type", ""),
            max_bytes=settings.image_upload_max_bytes,
            max_pixels=settings.image_upload_max_pixels,
            max_dimension=settings.image_upload_max_dimension,
        )
    except ImageValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    asset = ImageAssetService(
        UploadedImageAssetRepository(session), LocalObjectStorage(settings.object_storage_path)
    ).persist(sanitized)
    return UploadedImageResponse(
        asset_id=asset.id,
        media_type=asset.media_type,
        byte_size=asset.byte_size,
        width=asset.width,
        height=asset.height,
        content_sha256=asset.content_sha256,
    )
