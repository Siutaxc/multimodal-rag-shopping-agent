"""HTTP-isolated retrieval providers plus deterministic offline test substitutes."""

import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.resilience import (
    CircuitBreaker,
    CircuitOpenError,
    RetryPolicy,
    execute_with_resilience,
    shared_circuit_breaker,
)
from app.core.settings import Settings


class ProviderError(RuntimeError):
    """A provider failed without exposing secrets or untrusted response bodies."""


class ProviderTimeoutError(ProviderError):
    """A provider exceeded its configured HTTP timeout."""


class ProviderCircuitOpenError(ProviderError):
    """A provider call was skipped while its circuit breaker was open."""


@dataclass(frozen=True)
class ProviderIdentity:
    """Stable metadata persisted with vectors and emitted in query traces."""

    model_name: str
    model_version: str
    dimension: int | None = None

    @property
    def version_key(self) -> str:
        suffix = f":{self.dimension}" if self.dimension is not None else ""
        return f"{self.model_name}@{self.model_version}{suffix}"


class EmbeddingProvider(Protocol):
    """Batch text embedding contract used by indexing and query retrieval."""

    @property
    def identity(self) -> ProviderIdentity: ...

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]: ...


class RerankerProvider(Protocol):
    """Finite-list cross-encoder style scoring contract."""

    @property
    def identity(self) -> ProviderIdentity: ...

    def score(self, query: str, documents: Sequence[str]) -> list[float]: ...


_CONCEPT_ALIASES: tuple[tuple[str, ...], ...] = (
    ("通勤", "地铁", "公交", "出行", "travel", "commute", "城市"),
    ("降噪", "主动降噪", "anc", "noise cancellation", "低频环境噪声"),
    ("舒适", "戴眼镜", "眼镜", "不夹头", "头梁压力", "长时间佩戴", "可接受"),
    ("轻量", "轻便", "重量轻", "便携", "小型"),
    ("办公", "会议", "网课", "语音", "office", "work"),
    ("通话", "麦克风", "拾音", "话筒", "microphone", "语音清晰"),
    ("运动", "跑步", "户外", "健身", "run", "outdoor"),
    ("游泳", "防水", "雨天", "ip67", "ip68", "water"),
    ("续航长", "长续航", "一周", "电量", "battery", "续航"),
    ("开放", "不堵耳", "环境音", "open ear", "open-ear", "耳夹"),
    ("骨传导", "bone conduction", "bone_conduction"),
    ("头戴", "包耳", "over ear", "over-ear"),
    ("入耳", "in ear", "in-ear"),
    ("半入耳", "semi in ear", "semi-in-ear"),
    ("贴耳", "on ear", "on-ear"),
    ("无线", "蓝牙", "wireless", "bluetooth"),
    ("有线", "wired", "线控", "高阻抗"),
    ("声音", "音质", "人声", "低频", "sound", "reference"),
    ("折叠", "收纳", "旅行", "travel"),
)


class DeterministicEmbeddingProvider:
    """Stable semantic feature hashing for CI and offline Fixture demonstrations."""

    def __init__(self, identity: ProviderIdentity) -> None:
        if identity.dimension is None or identity.dimension < 128:
            raise ValueError("deterministic embeddings require a dimension of at least 128")
        self._identity = identity

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [_deterministic_vector(text, self._identity.dimension or 0) for text in texts]


class DeterministicRerankerProvider:
    """Offline pair scorer sharing the deterministic semantic representation."""

    def __init__(self, identity: ProviderIdentity, *, embedding_dimension: int = 1024) -> None:
        self._identity = identity
        self._embedder = DeterministicEmbeddingProvider(
            ProviderIdentity(
                "shoplens/fixture-pair-encoder",
                identity.model_version,
                embedding_dimension,
            )
        )

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        vectors = self._embedder.embed_texts([query, *documents])
        query_vector = vectors[0]
        return [
            sum(left * right for left, right in zip(query_vector, vector, strict=True))
            for vector in vectors[1:]
        ]


class BgeM3HttpEmbeddingProvider:
    """BGE-M3 adapter for OpenAI-compatible HTTP/HTTPS embedding endpoints."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str | None,
        identity: ProviderIdentity,
        timeout_seconds: float,
        client: httpx.Client | None = None,
        retry_policy: RetryPolicy | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        _validate_http_endpoint(endpoint)
        self._endpoint = endpoint
        self._identity = identity
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._retry_policy = retry_policy or RetryPolicy()
        self._breaker = circuit_breaker or CircuitBreaker(failure_threshold=3, recovery_seconds=30)

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = execute_with_resilience(
                "embedding",
                lambda: self._post({"model": self._identity.model_name, "input": list(texts)}),
                policy=self._retry_policy,
                breaker=self._breaker,
            )
            payload = response.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise ValueError("response data must be a list")
            vectors = [item.get("embedding") for item in data if isinstance(item, dict)]
            return _validated_vectors(vectors, len(texts), self._identity.dimension)
        except httpx.TimeoutException as error:
            raise ProviderTimeoutError("embedding provider timed out") from error
        except CircuitOpenError as error:
            raise ProviderCircuitOpenError("embedding provider circuit is open") from error
        except (httpx.HTTPError, TypeError, ValueError) as error:
            raise ProviderError("embedding provider returned an invalid response") from error

    def _post(self, payload: dict[str, object]) -> httpx.Response:
        response = self._client.post(self._endpoint, headers=self._headers, json=payload)
        response.raise_for_status()
        return response


class BgeRerankerHttpProvider:
    """BGE reranker adapter using a bounded HTTP/HTTPS JSON request."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str | None,
        identity: ProviderIdentity,
        timeout_seconds: float,
        client: httpx.Client | None = None,
        retry_policy: RetryPolicy | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        _validate_http_endpoint(endpoint)
        self._endpoint = endpoint
        self._identity = identity
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._retry_policy = retry_policy or RetryPolicy()
        self._breaker = circuit_breaker or CircuitBreaker(failure_threshold=3, recovery_seconds=30)

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        if not documents:
            return []
        try:
            response = execute_with_resilience(
                "reranker",
                lambda: self._post(
                    {
                        "model": self._identity.model_name,
                        "query": query,
                        "documents": list(documents),
                    }
                ),
                policy=self._retry_policy,
                breaker=self._breaker,
            )
            payload = response.json()
            return _reranker_scores(payload, len(documents))
        except httpx.TimeoutException as error:
            raise ProviderTimeoutError("reranker provider timed out") from error
        except CircuitOpenError as error:
            raise ProviderCircuitOpenError("reranker provider circuit is open") from error
        except (httpx.HTTPError, TypeError, ValueError) as error:
            raise ProviderError("reranker provider returned an invalid response") from error

    def _post(self, payload: dict[str, object]) -> httpx.Response:
        response = self._client.post(self._endpoint, headers=self._headers, json=payload)
        response.raise_for_status()
        return response


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    identity = ProviderIdentity(
        settings.embedding_model_name,
        settings.embedding_model_version,
        settings.embedding_dimension,
    )
    if settings.embedding_provider == "fixture":
        return DeterministicEmbeddingProvider(identity)
    assert settings.embedding_endpoint is not None
    return BgeM3HttpEmbeddingProvider(
        endpoint=str(settings.embedding_endpoint),
        api_key=settings.embedding_api_key,
        identity=identity,
        timeout_seconds=settings.embedding_timeout_seconds,
        retry_policy=RetryPolicy(
            settings.provider_retry_attempts, settings.provider_retry_backoff_seconds
        ),
        circuit_breaker=shared_circuit_breaker(
            f"embedding:{settings.embedding_endpoint}",
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_seconds=settings.circuit_breaker_recovery_seconds,
        ),
    )


def create_reranker_provider(settings: Settings) -> RerankerProvider:
    identity = ProviderIdentity(
        settings.reranker_model_name,
        settings.reranker_model_version,
    )
    if settings.reranker_provider == "fixture":
        return DeterministicRerankerProvider(
            identity, embedding_dimension=settings.embedding_dimension
        )
    assert settings.reranker_endpoint is not None
    return BgeRerankerHttpProvider(
        endpoint=str(settings.reranker_endpoint),
        api_key=settings.reranker_api_key,
        identity=identity,
        timeout_seconds=settings.reranker_timeout_seconds,
        retry_policy=RetryPolicy(
            settings.provider_retry_attempts, settings.provider_retry_backoff_seconds
        ),
        circuit_breaker=shared_circuit_breaker(
            f"reranker:{settings.reranker_endpoint}",
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_seconds=settings.circuit_breaker_recovery_seconds,
        ),
    )


def _deterministic_vector(text: str, dimension: int) -> list[float]:
    normalized = text.casefold()
    vector = [0.0] * dimension
    for index, aliases in enumerate(_CONCEPT_ALIASES):
        vector[index] = 3.0 * sum(alias in normalized for alias in aliases)
    tokens = re.findall(r"[a-z0-9]+|[\u3400-\u9fff]", normalized)
    tokens.extend(normalized[index : index + 2] for index in range(max(0, len(normalized) - 1)))
    offset = len(_CONCEPT_ALIASES)
    width = dimension - offset
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        vector[offset + int.from_bytes(digest[:4], "big") % width] += 0.35
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _validated_vectors(
    values: list[object], expected_count: int, dimension: int | None
) -> list[list[float]]:
    if len(values) != expected_count or dimension is None:
        raise ValueError("embedding count or dimension mismatch")
    result: list[list[float]] = []
    for value in values:
        if not isinstance(value, list) or len(value) != dimension:
            raise ValueError("embedding dimension mismatch")
        vector = [float(item) for item in value]
        if not all(math.isfinite(item) for item in vector):
            raise ValueError("embedding contains a non-finite value")
        result.append(vector)
    return result


def _reranker_scores(payload: object, expected_count: int) -> list[float]:
    if not isinstance(payload, dict):
        raise ValueError("reranker response must be an object")
    raw_scores = payload.get("scores")
    if isinstance(raw_scores, list):
        scores = [float(value) for value in raw_scores]
    else:
        results = payload.get("results")
        if not isinstance(results, list):
            raise ValueError("reranker response needs scores or results")
        ordered = sorted(
            (
                (int(item["index"]), float(item["relevance_score"]))
                for item in results
                if isinstance(item, dict)
            ),
            key=lambda item: item[0],
        )
        scores = [score for _, score in ordered]
    if len(scores) != expected_count or not all(math.isfinite(score) for score in scores):
        raise ValueError("reranker score count mismatch")
    return scores


def _validate_http_endpoint(endpoint: str) -> None:
    if not endpoint.startswith(("http://", "https://")):
        raise ValueError("provider endpoint must use HTTP or HTTPS")
