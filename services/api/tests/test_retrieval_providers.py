"""Provider contract tests are deterministic and never require a paid model API."""

import httpx
import pytest
from app.providers.retrieval import (
    BgeM3HttpEmbeddingProvider,
    BgeRerankerHttpProvider,
    DeterministicEmbeddingProvider,
    ProviderIdentity,
    ProviderTimeoutError,
)


def test_deterministic_embedding_is_stable_normalized_and_semantic() -> None:
    provider = DeterministicEmbeddingProvider(ProviderIdentity("BAAI/bge-m3", "test-v1", 1024))
    vectors = provider.embed_texts(
        ["地铁通勤需要主动降噪", "城市出行想减少环境噪声", "游泳训练防水"]
    )

    assert vectors[0] == provider.embed_texts(["地铁通勤需要主动降噪"])[0]
    assert sum(value * value for value in vectors[0]) == pytest.approx(1.0)
    related = sum(left * right for left, right in zip(vectors[0], vectors[1], strict=True))
    unrelated = sum(left * right for left, right in zip(vectors[0], vectors[2], strict=True))
    assert related > unrelated


def test_http_embedding_provider_validates_response_dimension() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"data": [{"embedding": [0.0] * 1024}]},
            request=request,
        )
    )
    provider = BgeM3HttpEmbeddingProvider(
        endpoint="https://provider.example/v1/embeddings",
        api_key="secret",
        identity=ProviderIdentity("BAAI/bge-m3", "remote-v1", 1024),
        timeout_seconds=1,
        client=httpx.Client(transport=transport),
    )

    vectors = provider.embed_texts(["test"])

    assert len(vectors) == 1
    assert len(vectors[0]) == 1024


def test_http_embedding_provider_maps_timeout_and_rejects_non_http() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("late", request=request)

    provider = BgeM3HttpEmbeddingProvider(
        endpoint="http://provider.example/v1/embeddings",
        api_key=None,
        identity=ProviderIdentity("BAAI/bge-m3", "remote-v1", 1024),
        timeout_seconds=1,
        client=httpx.Client(transport=httpx.MockTransport(timeout)),
    )
    with pytest.raises(ProviderTimeoutError):
        provider.embed_texts(["test"])
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        BgeM3HttpEmbeddingProvider(
            endpoint="ws://provider.example/embeddings",
            api_key=None,
            identity=ProviderIdentity("BAAI/bge-m3", "remote-v1", 1024),
            timeout_seconds=1,
        )


def test_http_reranker_restores_scores_to_document_order() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "results": [
                    {"index": 1, "relevance_score": 0.2},
                    {"index": 0, "relevance_score": 0.9},
                ]
            },
            request=request,
        )
    )
    provider = BgeRerankerHttpProvider(
        endpoint="https://provider.example/v1/rerank",
        api_key=None,
        identity=ProviderIdentity("BAAI/bge-reranker-v2-m3", "remote-v1"),
        timeout_seconds=1,
        client=httpx.Client(transport=transport),
    )

    assert provider.score("query", ["first", "second"]) == [0.9, 0.2]
