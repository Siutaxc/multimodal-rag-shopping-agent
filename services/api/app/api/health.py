"""Liveness and dependency readiness endpoints."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app import __version__
from app.core.readiness import DependencyProbe, ReadinessReport
from app.core.settings import Settings, get_settings

router = APIRouter(prefix="/health", tags=["health"])


class LiveResponse(BaseModel):
    """Stable response returned when the API process can serve requests."""

    status: Literal["ok"] = "ok"
    service: Literal["shoplens-api"] = "shoplens-api"
    version: str


class ReadyResponse(BaseModel):
    """Readiness response covering every required phase-one dependency."""

    status: Literal["ready", "not_ready"]
    checks: dict[str, Literal["ok", "unavailable", "missing"]]


def get_dependency_probe(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DependencyProbe:
    """Build a probe from validated application settings."""

    return DependencyProbe(settings)


@router.get("/live", response_model=LiveResponse, summary="API process liveness")
async def live() -> LiveResponse:
    """Return success without consulting external dependencies."""

    return LiveResponse(version=__version__)


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadyResponse}},
    summary="PostgreSQL, pgvector, and Redis readiness",
)
async def ready(
    probe: Annotated[DependencyProbe, Depends(get_dependency_probe)],
) -> ReadyResponse | JSONResponse:
    """Return 503 until every required dependency passes its probe."""

    report: ReadinessReport = await probe.check()
    response = ReadyResponse(
        status="ready" if report.ready else "not_ready",
        checks=report.checks,
    )
    if report.ready:
        return response
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response.model_dump(),
    )
