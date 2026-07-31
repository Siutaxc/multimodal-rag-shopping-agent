"""HTTP-only schema adapter contracts for the optional stage-six model provider."""

import json

import httpx
import pytest
from app.agent.schemas import EvidenceItem
from app.api.search import SearchFiltersInput
from app.providers.agent import HttpAgentModelProvider
from app.providers.retrieval import ProviderTimeoutError


def _provider(handler: httpx.MockTransport) -> HttpAgentModelProvider:
    return HttpAgentModelProvider(
        endpoint="https://provider.example/v1/chat/completions",
        api_key="secret",
        model_name="bounded-agent",
        model_version="v1",
        timeout_seconds=1,
        client=httpx.Client(transport=handler),
    )


def test_http_agent_parses_strict_json_without_tool_calls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["temperature"] == 0
        assert payload["response_format"] == {"type": "json_object"}
        assert request.headers["Authorization"] == "Bearer secret"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "intent": "recommend",
                                    "filters": {"price_max": "1000", "anc": True},
                                    "clear_fields": [],
                                    "clear_all": False,
                                    "clear_soft_preferences": False,
                                    "soft_preferences": ["适合通勤"],
                                    "referenced_product_ids": [],
                                }
                            )
                        }
                    }
                ]
            },
        )

    parsed = _provider(httpx.MockTransport(handler)).parse_request(
        "预算1000, 通勤降噪", SearchFiltersInput()
    )
    assert str(parsed.filters.price_max) == "1000"
    assert parsed.filters.anc is True


def test_http_agent_answer_plan_only_accepts_product_and_evidence_ids() -> None:
    evidence = EvidenceItem(
        id="fact:11111111-1111-1111-1111-111111111111:price_amount",
        product_id="11111111-1111-1111-1111-111111111111",
        kind="product_fact",
        field="price_amount",
        value="899.00",
        source_name="fixture",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        user_data = json.loads(body["messages"][1]["content"])
        assert user_data["untrusted_evidence_data"][0]["id"] == evidence.id
        return httpx.Response(
            200,
            json={
                "output": {
                    "recommendations": [
                        {
                            "product_id": str(evidence.product_id),
                            "evidence_ids": [evidence.id],
                        }
                    ]
                }
            },
        )

    plan = _provider(httpx.MockTransport(handler)).plan_answer(
        "推荐", [str(evidence.product_id)], [evidence]
    )
    assert plan.recommendations[0].evidence_ids == [evidence.id]


def test_http_agent_rejects_websocket_and_maps_timeout() -> None:
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        HttpAgentModelProvider(
            endpoint="wss://provider.example/agent",
            api_key=None,
            model_name="agent",
            model_version="v1",
            timeout_seconds=1,
        )

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("injected", request=request)

    with pytest.raises(ProviderTimeoutError):
        _provider(httpx.MockTransport(timeout)).parse_request("推荐耳机", SearchFiltersInput())
