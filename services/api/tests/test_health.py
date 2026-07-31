"""Unit tests for liveness, readiness, and OpenAPI behavior."""

from collections.abc import Iterator
from typing import cast

import pytest
from app.api.health import get_dependency_probe
from app.core.readiness import ReadinessReport
from app.core.settings import Settings
from app.main import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeProbe:
    """Deterministic readiness probe used to isolate route behavior."""

    def __init__(self, report: ReadinessReport) -> None:
        self._report = report

    async def check(self) -> ReadinessReport:
        return self._report


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(app_env="test", _env_file=None)
    application = create_app(settings)
    with TestClient(application) as test_client:
        yield test_client


def override_probe(application: FastAPI, report: ReadinessReport) -> None:
    """Install a typed FastAPI dependency override for a single test."""

    def probe_override() -> FakeProbe:
        return FakeProbe(report)

    application.dependency_overrides[get_dependency_probe] = probe_override


def test_liveness_is_available_at_versioned_and_compatibility_paths(
    client: TestClient,
) -> None:
    for path in ("/api/v1/health/live", "/health/live"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "service": "shoplens-api",
            "version": "0.4.0",
        }


def test_readiness_reports_all_dependencies(client: TestClient) -> None:
    override_probe(
        cast(FastAPI, client.app),
        ReadinessReport(checks={"postgres": "ok", "pgvector": "ok", "redis": "ok"}),
    )

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"postgres": "ok", "pgvector": "ok", "redis": "ok"},
    }


def test_readiness_returns_503_when_pgvector_is_missing(client: TestClient) -> None:
    override_probe(
        cast(FastAPI, client.app),
        ReadinessReport(checks={"postgres": "ok", "pgvector": "missing", "redis": "ok"}),
    )

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["pgvector"] == "missing"


def test_openapi_exposes_only_canonical_versioned_health_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health/live" in paths
    assert "/api/v1/health/ready" in paths
    assert "/api/v1/products" in paths
    assert "/api/v1/products/{product_id}" in paths
    assert "/health/live" not in paths
