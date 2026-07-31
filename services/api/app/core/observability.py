"""Structured request logging and bounded-cardinality HTTP instrumentation."""

import hashlib
import json
import logging
import re
from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.metrics import metrics

logger = logging.getLogger("shoplens.http")
_UUID_SEGMENT = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"
)
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")


def normalized_path(path: str) -> str:
    """Collapse opaque UUID path segments to avoid metric-label cardinality growth."""

    return _UUID_SEGMENT.sub("/{id}", path)


def query_fingerprint(statement: str) -> str:
    """Return a non-reversible identifier rather than logging SQL or bound values."""

    return hashlib.sha256(" ".join(statement.split()).encode("utf-8")).hexdigest()[:16]


class RequestObservabilityMiddleware:
    """Emit one JSON access event and Prometheus observations per HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = perf_counter()
        status_code = 500
        raw_headers = {key.lower(): value for key, value in scope.get("headers", [])}
        supplied = raw_headers.get(b"x-request-id", b"").decode("ascii", errors="ignore")
        request_id = supplied if _SAFE_REQUEST_ID.fullmatch(supplied) else str(uuid4())

        async def send_with_headers(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        finally:
            duration_ms = (perf_counter() - started) * 1000
            method = str(scope.get("method", "UNKNOWN"))
            path = normalized_path(str(scope.get("path", "")))
            labels = {"method": method, "path": path, "status": str(status_code)}
            metrics.counter(
                "shoplens_http_requests_total",
                labels=labels,
                help_text="HTTP requests served by ShopLens",
            )
            metrics.histogram(
                "shoplens_http_request_duration_ms",
                duration_ms,
                labels={"method": method, "path": path},
                help_text="HTTP request duration in milliseconds",
            )
            logger.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status": status_code,
                        "duration_ms": round(duration_ms, 3),
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
