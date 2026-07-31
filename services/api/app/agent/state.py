"""Opaque conversation and trace state stored in Redis with a test memory substitute."""

from typing import Protocol
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from app.agent.schemas import AgentTrace, SessionContext
from app.core.settings import Settings


class StateStoreError(RuntimeError):
    """State is optional for retrieval; callers can explicitly degrade on failure."""


class AgentStateStore(Protocol):
    def get_session(self, session_id: UUID) -> SessionContext | None: ...

    def save_session(self, context: SessionContext) -> None: ...

    def get_trace(self, trace_id: UUID) -> AgentTrace | None: ...

    def save_trace(self, trace: AgentTrace) -> None: ...


class RedisAgentStateStore:
    """Store only validated JSON under namespaced, opaque UUID keys."""

    def __init__(
        self,
        client: Redis,
        *,
        session_ttl_seconds: int,
        trace_ttl_seconds: int,
    ) -> None:
        self._client = client
        self._session_ttl = session_ttl_seconds
        self._trace_ttl = trace_ttl_seconds

    def get_session(self, session_id: UUID) -> SessionContext | None:
        raw = self._get(f"shoplens:agent:session:{session_id}")
        return SessionContext.model_validate_json(raw) if raw is not None else None

    def save_session(self, context: SessionContext) -> None:
        self._set(
            f"shoplens:agent:session:{context.session_id}",
            self._session_ttl,
            context.model_dump_json(),
        )

    def get_trace(self, trace_id: UUID) -> AgentTrace | None:
        raw = self._get(f"shoplens:agent:trace:{trace_id}")
        return AgentTrace.model_validate_json(raw) if raw is not None else None

    def save_trace(self, trace: AgentTrace) -> None:
        self._set(
            f"shoplens:agent:trace:{trace.trace_id}",
            self._trace_ttl,
            trace.model_dump_json(),
        )

    def _get(self, key: str) -> bytes | str | None:
        try:
            value = self._client.get(key)
        except (OSError, RedisError) as error:
            raise StateStoreError("agent state store is unavailable") from error
        if value is None or isinstance(value, (bytes, str)):
            return value
        raise StateStoreError("agent state store returned an invalid value")

    def _set(self, key: str, ttl: int, value: str) -> None:
        try:
            self._client.setex(key, ttl, value)
        except (OSError, RedisError) as error:
            raise StateStoreError("agent state store is unavailable") from error


class MemoryAgentStateStore:
    """Deterministic state store for unit tests; never shared with production wiring."""

    def __init__(self) -> None:
        self.sessions: dict[UUID, SessionContext] = {}
        self.traces: dict[UUID, AgentTrace] = {}

    def get_session(self, session_id: UUID) -> SessionContext | None:
        return self.sessions.get(session_id)

    def save_session(self, context: SessionContext) -> None:
        self.sessions[context.session_id] = context

    def get_trace(self, trace_id: UUID) -> AgentTrace | None:
        return self.traces.get(trace_id)

    def save_trace(self, trace: AgentTrace) -> None:
        self.traces[trace.trace_id] = trace


def create_agent_state_store(settings: Settings) -> AgentStateStore:
    timeout = settings.dependency_timeout_seconds
    client = Redis.from_url(
        str(settings.redis_url),
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
        decode_responses=False,
    )
    return RedisAgentStateStore(
        client,
        session_ttl_seconds=settings.agent_session_ttl_seconds,
        trace_ttl_seconds=settings.agent_trace_ttl_seconds,
    )
