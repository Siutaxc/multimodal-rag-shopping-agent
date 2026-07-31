"""SQLAlchemy engine and request-scoped session dependencies."""

import json
import logging
from collections.abc import Iterator
from functools import lru_cache
from time import perf_counter
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.metrics import metrics
from app.core.observability import query_fingerprint
from app.core.settings import Settings, get_settings

logger = logging.getLogger("shoplens.database")


def sqlalchemy_database_url(database_url: str) -> str:
    """Select psycopg 3 explicitly instead of SQLAlchemy's legacy default driver."""

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


@lru_cache(maxsize=8)
def get_engine(database_url: str, slow_query_threshold_ms: float = 100.0) -> Engine:
    """Create one checked connection pool per configured database URL."""

    engine = create_engine(sqlalchemy_database_url(database_url), pool_pre_ping=True)

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        _connection: object,
        _cursor: object,
        _statement: str,
        _parameters: object,
        context: Any,
        _executemany: bool,
    ) -> None:
        context._shoplens_started = perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        context: Any,
        _executemany: bool,
    ) -> None:
        started = getattr(context, "_shoplens_started", None)
        if not isinstance(started, float):
            return
        duration_ms = (perf_counter() - started) * 1000
        operation = (
            statement.lstrip().split(maxsplit=1)[0].upper() if statement.strip() else "UNKNOWN"
        )
        metrics.counter(
            "shoplens_db_queries_total",
            labels={"operation": operation},
            help_text="Database statements executed by operation",
        )
        metrics.histogram(
            "shoplens_db_query_duration_ms",
            duration_ms,
            labels={"operation": operation},
            help_text="Database statement duration in milliseconds",
        )
        if duration_ms >= slow_query_threshold_ms:
            metrics.counter(
                "shoplens_db_slow_queries_total",
                labels={"operation": operation},
                help_text="Database statements exceeding the configured threshold",
            )
            logger.warning(
                json.dumps(
                    {
                        "event": "slow_query",
                        "operation": operation,
                        "query_fingerprint": query_fingerprint(statement),
                        "duration_ms": round(duration_ms, 3),
                        "threshold_ms": slow_query_threshold_ms,
                    },
                    separators=(",", ":"),
                )
            )

    return engine


def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Iterator[Session]:
    """Yield a transaction-capable SQLAlchemy session for one HTTP request."""

    factory = sessionmaker(
        bind=get_engine(str(settings.database_url), settings.slow_query_threshold_ms),
        expire_on_commit=False,
        class_=Session,
    )
    with factory() as session:
        yield session
