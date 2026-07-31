"""Bounded retry and circuit-breaker primitives for HTTP/HTTPS providers."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import Lock
from time import monotonic, sleep

import httpx

from app.core.metrics import metrics


class CircuitOpenError(RuntimeError):
    """The dependency is temporarily blocked after consecutive failures."""


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 1
    backoff_seconds: float = 0.0


class CircuitBreaker:
    """Thread-safe closed/open/half-open breaker with one recovery probe."""

    def __init__(self, *, failure_threshold: int, recovery_seconds: float) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._failures = 0
        self._opened_at: float | None = None
        self._half_open_probe = False
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state(monotonic())

    def allow(self) -> None:
        with self._lock:
            state = self._state(monotonic())
            if state == CircuitState.OPEN:
                raise CircuitOpenError("provider circuit is open")
            if state == CircuitState.HALF_OPEN:
                if self._half_open_probe:
                    raise CircuitOpenError("provider circuit recovery probe is already running")
                self._half_open_probe = True

    def success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None
            self._half_open_probe = False

    def failure(self) -> None:
        with self._lock:
            self._half_open_probe = False
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_at = monotonic()

    def _state(self, now: float) -> CircuitState:
        if self._opened_at is None:
            return CircuitState.CLOSED
        if now - self._opened_at >= self.recovery_seconds:
            return CircuitState.HALF_OPEN
        return CircuitState.OPEN


_breakers: dict[str, CircuitBreaker] = {}
_breakers_lock = Lock()


def shared_circuit_breaker(
    key: str, *, failure_threshold: int, recovery_seconds: float
) -> CircuitBreaker:
    """Reuse breaker state across short-lived request-scoped provider adapters."""

    with _breakers_lock:
        breaker = _breakers.get(key)
        if breaker is None:
            breaker = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_seconds=recovery_seconds,
            )
            _breakers[key] = breaker
        return breaker


def execute_with_resilience[T](
    operation: str,
    action: Callable[[], T],
    *,
    policy: RetryPolicy,
    breaker: CircuitBreaker,
    sleeper: Callable[[float], None] = sleep,
) -> T:
    """Retry transient HTTP failures, then update circuit state exactly once."""

    try:
        breaker.allow()
    except CircuitOpenError:
        metrics.counter(
            "shoplens_provider_circuit_rejections_total",
            labels={"provider": operation},
            help_text="Provider calls rejected by an open circuit",
        )
        raise
    last_error: httpx.HTTPError | None = None
    for attempt in range(1, policy.attempts + 1):
        try:
            result = action()
            breaker.success()
            metrics.counter(
                "shoplens_provider_calls_total",
                labels={"provider": operation, "outcome": "success"},
                help_text="Remote provider attempts by final outcome",
            )
            return result
        except httpx.HTTPStatusError as error:
            last_error = error
            status = error.response.status_code
            retryable = status == 429 or status >= 500
            if not retryable or attempt == policy.attempts:
                break
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            last_error = error
            if attempt == policy.attempts:
                break
        if policy.backoff_seconds > 0:
            sleeper(policy.backoff_seconds * (2 ** (attempt - 1)))
        metrics.counter(
            "shoplens_provider_retries_total",
            labels={"provider": operation},
            help_text="Transient provider requests retried",
        )
    breaker.failure()
    metrics.counter(
        "shoplens_provider_calls_total",
        labels={"provider": operation, "outcome": "failure"},
        help_text="Remote provider attempts by final outcome",
    )
    assert last_error is not None
    raise last_error
