"""SigLIP2-style image embedding providers with an offline visual CI substitute."""

import base64
import io
import math
from collections.abc import Sequence
from typing import Protocol, cast

import httpx
from PIL import Image, ImageOps

from app.core.resilience import (
    CircuitBreaker,
    CircuitOpenError,
    RetryPolicy,
    execute_with_resilience,
    shared_circuit_breaker,
)
from app.core.settings import Settings
from app.providers.retrieval import (
    ProviderCircuitOpenError,
    ProviderError,
    ProviderIdentity,
    ProviderTimeoutError,
)


class ImageEmbeddingProvider(Protocol):
    """Batch image embedding contract shared by indexing and uploaded queries."""

    @property
    def identity(self) -> ProviderIdentity: ...

    def embed_images(self, images: Sequence[bytes]) -> list[list[float]]: ...


class DeterministicImageEmbeddingProvider:
    """Stable pixel-feature encoder for CI; it is not presented as real SigLIP2 quality."""

    def __init__(self, identity: ProviderIdentity) -> None:
        if identity.dimension != 768:
            raise ValueError("deterministic image embeddings require exactly 768 dimensions")
        self._identity = identity

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    def embed_images(self, images: Sequence[bytes]) -> list[list[float]]:
        try:
            return [_visual_fixture_vector(content) for content in images]
        except (OSError, ValueError) as error:
            raise ProviderError("image provider could not decode sanitized image bytes") from error


class Siglip2HttpImageEmbeddingProvider:
    """Bounded HTTP/HTTPS adapter for a JSON SigLIP2 image embedding endpoint."""

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
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("provider endpoint must use HTTP or HTTPS")
        self._endpoint = endpoint
        self._identity = identity
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._retry_policy = retry_policy or RetryPolicy()
        self._breaker = circuit_breaker or CircuitBreaker(failure_threshold=3, recovery_seconds=30)

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    def embed_images(self, images: Sequence[bytes]) -> list[list[float]]:
        if not images:
            return []
        try:
            response = execute_with_resilience(
                "image_embedding",
                lambda: self._post(
                    {
                        "model": self._identity.model_name,
                        "images": [base64.b64encode(content).decode("ascii") for content in images],
                    }
                ),
                policy=self._retry_policy,
                breaker=self._breaker,
            )
            payload = response.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise ValueError("response data must be a list")
            vectors = [item.get("embedding") for item in data if isinstance(item, dict)]
            return _validated_vectors(vectors, len(images), self._identity.dimension)
        except httpx.TimeoutException as error:
            raise ProviderTimeoutError("image embedding provider timed out") from error
        except CircuitOpenError as error:
            raise ProviderCircuitOpenError("image embedding provider circuit is open") from error
        except (httpx.HTTPError, TypeError, ValueError) as error:
            raise ProviderError("image embedding provider returned an invalid response") from error

    def _post(self, payload: dict[str, object]) -> httpx.Response:
        response = self._client.post(self._endpoint, headers=self._headers, json=payload)
        response.raise_for_status()
        return response


def create_image_embedding_provider(settings: Settings) -> ImageEmbeddingProvider:
    """Create the configured image provider without reading secrets outside settings."""

    identity = ProviderIdentity(
        settings.image_embedding_model_name,
        settings.image_embedding_model_version,
        settings.image_embedding_dimension,
    )
    if settings.image_embedding_provider == "fixture":
        return DeterministicImageEmbeddingProvider(identity)
    assert settings.image_embedding_endpoint is not None
    return Siglip2HttpImageEmbeddingProvider(
        endpoint=str(settings.image_embedding_endpoint),
        api_key=settings.image_embedding_api_key,
        identity=identity,
        timeout_seconds=settings.image_embedding_timeout_seconds,
        retry_policy=RetryPolicy(
            settings.provider_retry_attempts, settings.provider_retry_backoff_seconds
        ),
        circuit_breaker=shared_circuit_breaker(
            f"image_embedding:{settings.image_embedding_endpoint}",
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_seconds=settings.circuit_breaker_recovery_seconds,
        ),
    )


def _visual_fixture_vector(content: bytes) -> list[float]:
    with Image.open(io.BytesIO(content)) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        grid = image.resize((12, 12), Image.Resampling.LANCZOS)
        grid_pixels = cast(list[tuple[int, int, int]], list(grid.get_flattened_data()))
        values = [channel / 255.0 for pixel in grid_pixels for channel in pixel]

        histograms = grid.histogram()
        for channel in range(3):
            channel_histogram = histograms[channel * 256 : (channel + 1) * 256]
            for bucket in range(16):
                values.append(sum(channel_histogram[bucket * 16 : (bucket + 1) * 16]) / 144.0)

        grayscale = image.convert("L").resize((16, 16), Image.Resampling.LANCZOS)
        grayscale_pixels = cast(list[int], list(grayscale.get_flattened_data()))
        gray_values = [value / 255.0 for value in grayscale_pixels]
        for row in range(16):
            for column in range(16):
                current = gray_values[row * 16 + column]
                right = gray_values[row * 16 + min(column + 1, 15)]
                below = gray_values[min(row + 1, 15) * 16 + column]
                values.append(abs(current - right) + abs(current - below))

        width, height = image.size
        aspect = width / height
        means = [
            sum(pixel[channel] for pixel in grid_pixels) / (144 * 255.0) for channel in range(3)
        ]
        extras = [min(aspect, 4.0) / 4.0, min(1.0 / aspect, 4.0) / 4.0, *means]
        values.extend((extras * 7)[:32])

    if len(values) != 768:
        raise ValueError("fixture visual feature dimension mismatch")
    centered = [value - 0.5 for value in values]
    norm = math.sqrt(sum(value * value for value in centered))
    if norm == 0:
        return centered
    return [value / norm for value in centered]


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
