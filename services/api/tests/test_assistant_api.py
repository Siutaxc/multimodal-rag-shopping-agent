"""HTTP contracts for agent query, compare, isolated sessions, and traces."""

from collections.abc import Iterator

import pytest
from app.agent.service import BoundedShoppingAgent
from app.agent.state import MemoryAgentStateStore
from app.api.assistant import get_agent_state_store, get_bounded_agent
from app.core.settings import Settings
from app.main import create_app
from app.providers.agent import DeterministicAgentModelProvider
from fastapi.testclient import TestClient

from .agent_helpers import FakeAgentTools, make_product


@pytest.fixture
def assistant_client() -> Iterator[tuple[TestClient, MemoryAgentStateStore, FakeAgentTools]]:
    products = [make_product(1), make_product(2)]
    tools = FakeAgentTools(products)
    state = MemoryAgentStateStore()
    settings = Settings(app_env="test", _env_file=None)
    agent = BoundedShoppingAgent(
        tools,
        state,
        DeterministicAgentModelProvider("fixture@v1"),
        settings,
    )
    application = create_app(settings)
    application.dependency_overrides[get_bounded_agent] = lambda: agent
    application.dependency_overrides[get_agent_state_store] = lambda: state
    with TestClient(application) as client:
        yield client, state, tools


def test_assistant_query_returns_structured_cards_evidence_and_trace(
    assistant_client: tuple[TestClient, MemoryAgentStateStore, FakeAgentTools],
) -> None:
    client, state, _ = assistant_client
    response = client.post(
        "/api/v1/assistant/query",
        json={"message": "预算 1000 元以内, 头戴式主动降噪, 通勤"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"]
    assert body["evidence"]
    assert body["trace"]["citation_validation"]["valid"] is True
    assert len(body["trace"]["tool_steps"]) <= 4

    session = client.get(f"/api/v1/sessions/{body['session_id']}")
    trace = client.get(f"/api/v1/traces/{body['trace_id']}")
    assert session.status_code == 200
    assert session.json()["filters"]["price_max"] == "1000"
    assert trace.status_code == 200
    assert body["trace_id"] in {str(value) for value in state.traces}


def test_compare_endpoint_returns_uniform_fact_rows(
    assistant_client: tuple[TestClient, MemoryAgentStateStore, FakeAgentTools],
) -> None:
    client, _, tools = assistant_client
    response = client.post(
        "/api/v1/products/compare",
        json={"product_ids": [str(product.id) for product in tools.products]},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["comparison"]["product_ids"]) == 2
    assert any(row["field"] == "price_amount" for row in body["comparison"]["rows"])


@pytest.mark.parametrize(
    "payload",
    [
        {"message": "   "},
        {"message": "推荐", "sql": "DROP TABLE products"},
        {"message": "推荐", "filters": {"raw_where": "1=1"}},
    ],
)
def test_assistant_rejects_blank_or_non_whitelisted_input(
    assistant_client: tuple[TestClient, MemoryAgentStateStore, FakeAgentTools],
    payload: dict[str, object],
) -> None:
    client, _, tools = assistant_client
    tools.calls.clear()
    response = client.post("/api/v1/assistant/query", json=payload)

    assert response.status_code == 422
    assert tools.calls == []
