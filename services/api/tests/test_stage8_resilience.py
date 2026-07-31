"""Stage-eight cache, rate-limit, retry, circuit, and metrics fault injection."""

from collections.abc import Iterator
from typing import cast

import httpx
import pytest
from app.core.cache import RedisResponseCache
from app.core.metrics import MetricsRegistry
from app.core.rate_limit import MemoryRateLimitStore, RateLimitMiddleware
from app.core.resilience import (
    CircuitBreaker,
    CircuitOpenError,
    RetryPolicy,
    execute_with_resilience,
)
from app.core.settings import Settings
from app.main import create_app
from app.providers.retrieval import BgeM3HttpEmbeddingProvider, ProviderIdentity
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis import Redis
from redis.exceptions import RedisError


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.fail = False

    def get(self, key: str) -> str | None:
        if self.fail:
            raise RedisError("injected")
        return self.values.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        if self.fail:
            raise RedisError("injected")
        self.values[key] = value
        self.ttls[key] = ttl


class UnavailableRateLimitStore:
    def increment(self, key: str, ttl_seconds: int) -> int | None:
        return None


def test_redis_cache_hit_expiry_contract_and_fail_open() -> None:
    redis = FakeRedis()
    cache = RedisResponseCache(cast(Redis, redis), namespace="test-v1", ttl_seconds=7)

    cache.set("abc", '{"ok":true}')
    assert cache.get("abc") == '{"ok":true}'
    assert redis.ttls["shoplens:cache:test-v1:abc"] == 7

    del redis.values["shoplens:cache:test-v1:abc"]
    assert cache.get("abc") is None
    redis.fail = True
    assert cache.get("abc") is None
    cache.set("abc", "ignored")


def test_provider_retries_transient_http_failures_then_succeeds() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            json={"data": [{"embedding": [0.0] * 1024}]},
            request=request,
        )

    provider = BgeM3HttpEmbeddingProvider(
        endpoint="https://provider.example/v1/embeddings",
        api_key=None,
        identity=ProviderIdentity("BAAI/bge-m3", "retry-test", 1024),
        timeout_seconds=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        retry_policy=RetryPolicy(attempts=3, backoff_seconds=0),
    )

    assert len(provider.embed_texts(["retry"])[0]) == 1024
    assert attempts == 3


def test_circuit_opens_and_rejects_without_running_action() -> None:
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=60)
    calls = 0

    def fail() -> None:
        nonlocal calls
        calls += 1
        request = httpx.Request("GET", "https://provider.example")
        raise httpx.ConnectError("injected", request=request)

    for _ in range(2):
        with pytest.raises(httpx.ConnectError):
            execute_with_resilience("test", fail, policy=RetryPolicy(), breaker=breaker)
    with pytest.raises(CircuitOpenError):
        execute_with_resilience("test", fail, policy=RetryPolicy(), breaker=breaker)
    assert calls == 2


@pytest.fixture
def limited_client() -> Iterator[TestClient]:
    app = FastAPI()

    @app.post("/expensive")
    def expensive() -> dict[str, bool]:
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        settings=Settings(
            app_env="test",
            rate_limit_enabled=True,
            rate_limit_requests=2,
            rate_limit_window_seconds=60,
            _env_file=None,
        ),
        store=MemoryRateLimitStore(),
    )
    with TestClient(app) as client:
        yield client


def test_rate_limit_allows_window_then_returns_retry_after(
    limited_client: TestClient,
) -> None:
    assert limited_client.post("/expensive").status_code == 200
    assert limited_client.post("/expensive").status_code == 200
    rejected = limited_client.post("/expensive")
    assert rejected.status_code == 429
    assert int(rejected.headers["Retry-After"]) >= 1


def test_rate_limit_store_failure_is_fail_open() -> None:
    app = FastAPI()

    @app.post("/expensive")
    def expensive() -> dict[str, bool]:
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        settings=Settings(
            app_env="test",
            rate_limit_enabled=True,
            rate_limit_requests=1,
            _env_file=None,
        ),
        store=UnavailableRateLimitStore(),
    )
    with TestClient(app) as client:
        assert client.post("/expensive").status_code == 200
        assert client.post("/expensive").status_code == 200


def test_metrics_endpoint_exports_request_histogram_and_request_id() -> None:
    application = create_app(
        Settings(
            app_env="test",
            cache_enabled=False,
            rate_limit_enabled=False,
            _env_file=None,
        )
    )
    with TestClient(application) as client:
        live = client.get("/api/v1/health/live", headers={"X-Request-ID": "stage8-test"})
        scrape = client.get("/metrics")

    assert live.headers["X-Request-ID"] == "stage8-test"
    assert scrape.status_code == 200
    assert "shoplens_http_requests_total" in scrape.text
    assert "shoplens_http_request_duration_ms_bucket" in scrape.text


def test_prometheus_labels_are_escaped() -> None:
    registry = MetricsRegistry()
    registry.counter("shoplens_test_total", labels={"value": 'a"b\\c'})
    assert 'value="a\\"b\\\\c"' in registry.render()
