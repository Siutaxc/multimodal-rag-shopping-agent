"""Redis fixed-window request limiting with a safe fail-open degradation path."""

import hashlib
import math
import time
from typing import Protocol

from redis import Redis
from redis.exceptions import RedisError
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.metrics import metrics
from app.core.observability import normalized_path
from app.core.settings import Settings


class RateLimitStore(Protocol):
    def increment(self, key: str, ttl_seconds: int) -> int | None: ...


class NullRateLimitStore:
    def increment(self, key: str, ttl_seconds: int) -> int | None:
        return 1


class RedisRateLimitStore:
    def __init__(self, client: Redis) -> None:
        self._client = client

    def increment(self, key: str, ttl_seconds: int) -> int | None:
        try:
            with self._client.pipeline(transaction=True) as pipeline:
                pipeline.incr(key)
                pipeline.expire(key, ttl_seconds, nx=True)
                count, _ = pipeline.execute()
            return int(count)
        except (OSError, RedisError):
            metrics.counter(
                "shoplens_rate_limit_store_errors_total",
                help_text="Rate-limit checks degraded because Redis was unavailable",
            )
            return None


class MemoryRateLimitStore:
    """Window-aware deterministic store for middleware tests."""

    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    def increment(self, key: str, ttl_seconds: int) -> int | None:
        value = self.values.get(key, 0) + 1
        self.values[key] = value
        return value


def create_rate_limit_store(settings: Settings) -> RateLimitStore:
    if not settings.rate_limit_enabled or settings.app_env == "test":
        return NullRateLimitStore()
    timeout = settings.dependency_timeout_seconds
    return RedisRateLimitStore(
        Redis.from_url(
            str(settings.redis_url),
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
            decode_responses=False,
        )
    )


class RateLimitMiddleware:
    """Protect mutating/expensive API calls while leaving health and metrics available."""

    def __init__(self, app: ASGIApp, settings: Settings, store: RateLimitStore) -> None:
        self.app = app
        self._enabled = settings.rate_limit_enabled
        self._limit = settings.rate_limit_requests
        self._window = settings.rate_limit_window_seconds
        self._store = store

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        method = str(scope.get("method", ""))
        path = str(scope.get("path", ""))
        if scope["type"] != "http" or not self._enabled or method not in {"POST", "PUT"}:
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        client_host = str(client[0]) if isinstance(client, tuple) and client else "unknown"
        identity = hashlib.sha256(client_host.encode("utf-8")).hexdigest()[:16]
        now = time.time()
        window_id = math.floor(now / self._window)
        key = f"shoplens:rate:{identity}:{method}:{normalized_path(path)}:{window_id}"
        count = self._store.increment(key, self._window + 1)
        if count is not None and count > self._limit:
            metrics.counter(
                "shoplens_rate_limit_rejections_total",
                labels={"method": method, "path": normalized_path(path)},
                help_text="Requests rejected by the fixed-window rate limiter",
            )
            retry_after = max(1, math.ceil(self._window - (now % self._window)))
            response = JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
