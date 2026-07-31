"""Tests for strict environment configuration validation."""

import pytest
from app.core.settings import Settings
from pydantic import ValidationError


def test_local_dependency_defaults_match_loopback_compose_bind() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url.hosts()[0]["host"] == "127.0.0.1"
    assert settings.redis_url.host == "127.0.0.1"


def test_settings_reject_database_url_with_wrong_scheme() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="http://localhost:5432/shoplens", _env_file=None)


def test_settings_reject_redis_url_with_wrong_scheme() -> None:
    with pytest.raises(ValidationError):
        Settings(redis_url="http://localhost:6379/0", _env_file=None)


def test_settings_reject_non_positive_dependency_timeout() -> None:
    with pytest.raises(ValidationError):
        Settings(dependency_timeout_seconds=0, _env_file=None)


def test_remote_providers_require_http_endpoints() -> None:
    with pytest.raises(ValidationError, match="embedding_endpoint"):
        Settings(embedding_provider="http", _env_file=None)
    with pytest.raises(ValidationError, match="reranker_endpoint"):
        Settings(reranker_provider="http", _env_file=None)
    with pytest.raises(ValidationError, match="image_embedding_endpoint"):
        Settings(image_embedding_provider="http", _env_file=None)
    with pytest.raises(ValidationError, match="agent_endpoint"):
        Settings(agent_provider="http", _env_file=None)


def test_websocket_provider_endpoints_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            embedding_provider="http",
            embedding_endpoint="ws://provider.example/embeddings",
            _env_file=None,
        )


def test_cors_origins_accept_http_and_https_only() -> None:
    settings = Settings(
        cors_allowed_origins=["http://localhost:3300", "https://shoplens.example"],
        _env_file=None,
    )

    assert [str(origin).rstrip("/") for origin in settings.cors_allowed_origins] == [
        "http://localhost:3300",
        "https://shoplens.example",
    ]
    with pytest.raises(ValidationError):
        Settings(cors_allowed_origins=["ws://shoplens.example"], _env_file=None)
    with pytest.raises(ValidationError):
        Settings(
            image_embedding_provider="http",
            image_embedding_endpoint="wss://provider.example/images",
            _env_file=None,
        )
    with pytest.raises(ValidationError):
        Settings(
            agent_provider="http",
            agent_endpoint="wss://provider.example/agent",
            _env_file=None,
        )


def test_fixture_mode_accepts_empty_optional_compose_values() -> None:
    settings = Settings(
        embedding_endpoint="",
        embedding_api_key="",
        reranker_endpoint="",
        reranker_api_key="",
        image_embedding_endpoint="",
        image_embedding_api_key="",
        agent_endpoint="",
        agent_api_key="",
        _env_file=None,
    )

    assert settings.embedding_endpoint is None
    assert settings.embedding_api_key is None
    assert settings.reranker_endpoint is None
    assert settings.reranker_api_key is None
    assert settings.image_embedding_endpoint is None
    assert settings.image_embedding_api_key is None
    assert settings.agent_endpoint is None
    assert settings.agent_api_key is None
