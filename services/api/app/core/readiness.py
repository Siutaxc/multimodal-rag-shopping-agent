"""Concrete PostgreSQL, pgvector, and Redis readiness probes."""

import asyncio
import math
from dataclasses import dataclass
from typing import Literal

import psycopg
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.settings import Settings

CheckState = Literal["ok", "unavailable", "missing"]


@dataclass(frozen=True)
class ReadinessReport:
    """Aggregated dependency state used by the HTTP route and integration tests."""

    checks: dict[str, CheckState]

    @property
    def ready(self) -> bool:
        """A service is ready only when every check reports success."""

        return bool(self.checks) and all(value == "ok" for value in self.checks.values())


class DependencyProbe:
    """Probe required services concurrently with bounded latency."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check(self) -> ReadinessReport:
        """Check PostgreSQL/pgvector and Redis without raising to the caller."""

        postgres_checks, redis_checks = await asyncio.gather(
            self._check_postgres(),
            self._check_redis(),
        )
        return ReadinessReport(checks={**postgres_checks, **redis_checks})

    async def _check_postgres(self) -> dict[str, CheckState]:
        timeout = self._settings.dependency_timeout_seconds
        connect_timeout = max(1, math.ceil(timeout))
        try:
            async with asyncio.timeout(timeout):
                vector_enabled = await asyncio.to_thread(
                    self._probe_postgres,
                    connect_timeout,
                )
            return {
                "postgres": "ok",
                "pgvector": "ok" if vector_enabled else "missing",
            }
        except (TimeoutError, psycopg.Error, OSError):
            return {"postgres": "unavailable", "pgvector": "unavailable"}

    def _probe_postgres(self, connect_timeout: int) -> bool:
        """Run the blocking psycopg probe outside the event loop.

        Psycopg's async connection does not support Windows' default Proactor
        event loop, while the synchronous connection is portable across the
        Windows development host and Linux containers.
        """

        with (
            psycopg.connect(
                str(self._settings.database_url),
                connect_timeout=connect_timeout,
            ) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT 1")
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            row = cursor.fetchone()
        return bool(row and row[0])

    async def _check_redis(self) -> dict[str, CheckState]:
        timeout = self._settings.dependency_timeout_seconds
        client: Redis = Redis.from_url(
            str(self._settings.redis_url),
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        try:
            async with asyncio.timeout(timeout):
                pong = await client.ping()
            return {"redis": "ok" if pong else "unavailable"}
        except (TimeoutError, OSError, RedisError):
            return {"redis": "unavailable"}
        finally:
            await client.aclose()
