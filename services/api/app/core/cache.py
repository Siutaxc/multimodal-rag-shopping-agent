"""Versioned Redis response cache with explicit fail-open behavior."""

import hashlib
import json
from functools import lru_cache
from typing import Protocol

from pydantic import BaseModel
from redis import Redis
from redis.exceptions import RedisError

from app.core.metrics import metrics
from app.core.settings import Settings


class ResponseCache(Protocol):
    def get(self, key: str) -> str | None: ...

    def set(self, key: str, value: str) -> None: ...


class NullResponseCache:
    def get(self, key: str) -> str | None:
        return None

    def set(self, key: str, value: str) -> None:
        return None


class RedisResponseCache:
    """Cache validated response JSON; Redis errors never fail a search request."""

    def __init__(self, client: Redis, *, namespace: str, ttl_seconds: int) -> None:
        self._client = client
        self._namespace = namespace
        self._ttl = ttl_seconds

    def _key(self, key: str) -> str:
        return f"shoplens:cache:{self._namespace}:{key}"

    def get(self, key: str) -> str | None:
        try:
            raw = self._client.get(self._key(key))
        except (OSError, RedisError):
            metrics.counter(
                "shoplens_cache_operations_total",
                labels={"operation": "get", "outcome": "error"},
                help_text="Response-cache operations by outcome",
            )
            return None
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        if isinstance(raw, str):
            return raw
        return None

    def set(self, key: str, value: str) -> None:
        try:
            self._client.setex(self._key(key), self._ttl, value)
            metrics.counter(
                "shoplens_cache_operations_total",
                labels={"operation": "set", "outcome": "success"},
                help_text="Response-cache operations by outcome",
            )
        except (OSError, RedisError):
            metrics.counter(
                "shoplens_cache_operations_total",
                labels={"operation": "set", "outcome": "error"},
                help_text="Response-cache operations by outcome",
            )


class MemoryResponseCache:
    """Deterministic cache substitute used by unit and fault-injection tests."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value


def cache_key(kind: str, request: BaseModel, settings: Settings) -> str:
    """Bind entries to request data and every model/document identity affecting results."""

    identity = {
        "kind": kind,
        "request": request.model_dump(mode="json"),
        "embedding": [settings.embedding_model_name, settings.embedding_model_version],
        "reranker": [settings.reranker_model_name, settings.reranker_model_version],
        "image": [settings.image_embedding_model_name, settings.image_embedding_model_version],
    }
    canonical = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_response_cache(settings: Settings) -> ResponseCache:
    if not settings.cache_enabled or settings.app_env == "test":
        return NullResponseCache()
    return _redis_response_cache(
        str(settings.redis_url),
        settings.dependency_timeout_seconds,
        settings.cache_namespace,
        settings.cache_ttl_seconds,
    )


@lru_cache(maxsize=8)
def _redis_response_cache(
    redis_url: str, timeout: float, namespace: str, ttl_seconds: int
) -> RedisResponseCache:
    client = Redis.from_url(
        redis_url,
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
        decode_responses=False,
    )
    return RedisResponseCache(
        client, namespace=namespace, ttl_seconds=ttl_seconds
    )
