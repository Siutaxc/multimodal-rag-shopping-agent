"""Smoke test for the Docker Compose PostgreSQL/pgvector and Redis services."""

import os

import pytest
from app.core.readiness import DependencyProbe
from app.core.settings import Settings


@pytest.mark.integration
async def test_compose_dependencies_are_ready() -> None:
    if os.environ.get("SHOPLENS_RUN_INTEGRATION") != "1":
        pytest.skip("set SHOPLENS_RUN_INTEGRATION=1 to test running infrastructure")

    report = await DependencyProbe(Settings(_env_file=None)).check()

    assert report.ready, report.checks
    assert report.checks == {"postgres": "ok", "pgvector": "ok", "redis": "ok"}
