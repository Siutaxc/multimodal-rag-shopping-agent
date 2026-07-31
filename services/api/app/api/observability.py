"""Prometheus scrape endpoint; no session or product data is exposed."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.metrics import metrics

router = APIRouter(tags=["observability"])


@router.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
def prometheus_metrics() -> PlainTextResponse:
    return PlainTextResponse(
        metrics.render(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )
