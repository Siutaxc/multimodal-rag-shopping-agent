"""Image provider contracts stay deterministic and HTTP-only in CI."""

from pathlib import Path

import httpx
import pytest
from app.providers.images import (
    DeterministicImageEmbeddingProvider,
    Siglip2HttpImageEmbeddingProvider,
)
from app.providers.retrieval import ProviderIdentity, ProviderTimeoutError

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def _fixture(name: str) -> bytes:
    return (WORKSPACE_ROOT / "data" / "fixtures" / "images" / name).read_bytes()


def test_deterministic_image_embedding_is_stable_normalized_and_visual() -> None:
    provider = DeterministicImageEmbeddingProvider(ProviderIdentity("siglip2", "test-v1", 768))
    first, same_category, different_category = provider.embed_images(
        [
            _fixture("fixture-001.png"),
            _fixture("fixture-006.png"),
            _fixture("fixture-014.png"),
        ]
    )

    assert first == provider.embed_images([_fixture("fixture-001.png")])[0]
    assert sum(value * value for value in first) == pytest.approx(1.0)
    over_ear_similarity = sum(
        left * right for left, right in zip(first, same_category, strict=True)
    )
    in_ear_similarity = sum(
        left * right for left, right in zip(first, different_category, strict=True)
    )
    assert over_ear_similarity > in_ear_similarity


def test_http_image_provider_validates_dimensions_and_maps_timeout() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"data": [{"embedding": [0.0] * 768}]}, request=request
        )
    )
    provider = Siglip2HttpImageEmbeddingProvider(
        endpoint="https://provider.example/v1/image-embeddings",
        api_key="secret",
        identity=ProviderIdentity("google/siglip2-base-patch16-224", "remote-v1", 768),
        timeout_seconds=1,
        client=httpx.Client(transport=transport),
    )
    assert len(provider.embed_images([b"safe-sanitized-bytes"])[0]) == 768

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("late", request=request)

    timed_out = Siglip2HttpImageEmbeddingProvider(
        endpoint="http://provider.example/v1/image-embeddings",
        api_key=None,
        identity=ProviderIdentity("siglip2", "remote-v1", 768),
        timeout_seconds=1,
        client=httpx.Client(transport=httpx.MockTransport(timeout)),
    )
    with pytest.raises(ProviderTimeoutError):
        timed_out.embed_images([b"bytes"])
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        Siglip2HttpImageEmbeddingProvider(
            endpoint="ws://provider.example/images",
            api_key=None,
            identity=ProviderIdentity("siglip2", "remote-v1", 768),
            timeout_seconds=1,
        )
