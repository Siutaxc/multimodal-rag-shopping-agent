"""Evidence-grounding and bounded-agent metrics with complete per-turn traces."""

import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from typing import Any
from uuid import UUID

from app.agent.schemas import AssistantResponse
from app.agent.service import BoundedShoppingAgent
from app.evaluation.stage6_schemas import Stage6Dataset


@dataclass(frozen=True)
class AgentCaseResult:
    id: str
    conversation_id: str
    status: str
    task_complete: bool
    condition_correct: bool
    tool_selection_correct: bool
    tool_count: int
    fact_claims: int
    fact_hallucinations: int
    cited_statements: int
    grounded_statements: int
    citation_count: int
    valid_citations: int
    degraded_reasons: list[str]
    latency_ms: float


@dataclass(frozen=True)
class Stage6AgentReport:
    dataset_name: str
    dataset_version: str
    generated_at: str
    corpus_product_count: int
    case_count: int
    task_completion_rate: float
    tool_selection_accuracy: float
    citation_precision: float
    citation_coverage: float
    structured_fact_claim_count: int
    structured_fact_hallucination_rate: float
    condition_mutation_accuracy: float
    average_tool_calls: float
    maximum_tool_calls: int
    invalid_loop_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    limitations: list[str]
    cases: list[AgentCaseResult]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Stage6EvaluationRunner:
    def __init__(self, agent: BoundedShoppingAgent) -> None:
        self._agent = agent

    def run(self, dataset: Stage6Dataset) -> Stage6AgentReport:
        session_ids: dict[str, UUID] = {}
        previous_product_ids: dict[str, list[UUID]] = {}
        results: list[AgentCaseResult] = []
        invalid_loops = 0
        for case in dataset.cases:
            session_id = session_ids.get(case.conversation_id)
            product_ids = (
                previous_product_ids.get(case.conversation_id, [])
                if case.action == "compare_previous"
                else []
            )
            response = self._agent.query(
                case.message,
                session_id=session_id,
                product_ids=product_ids,
            )
            session_ids[case.conversation_id] = response.session_id
            if response.recommendations:
                previous_product_ids[case.conversation_id] = [
                    item.product.id for item in response.recommendations
                ]
            tools = [step.tool for step in response.trace.tool_steps]
            if len(tools) != len(set(tools)):
                invalid_loops += 1
            facts, hallucinations = _fact_accuracy(response)
            cited, grounded, citation_count, valid_citations = _citation_accuracy(response)
            expected_filters = case.expected_filters.model_dump(mode="json", exclude_none=True)
            actual_filters = response.applied_filters.model_dump(mode="json", exclude_none=True)
            task_complete = (
                response.status == case.expected_status
                and len(response.recommendations) >= case.minimum_recommendations
                and response.trace.parsed_turn.intent == case.expected_intent
            )
            results.append(
                AgentCaseResult(
                    id=case.id,
                    conversation_id=case.conversation_id,
                    status=response.status,
                    task_complete=task_complete,
                    condition_correct=actual_filters == expected_filters,
                    tool_selection_correct=tools == case.expected_tools,
                    tool_count=len(tools),
                    fact_claims=facts,
                    fact_hallucinations=hallucinations,
                    cited_statements=cited,
                    grounded_statements=grounded,
                    citation_count=citation_count,
                    valid_citations=valid_citations,
                    degraded_reasons=response.trace.degraded_reasons,
                    latency_ms=response.trace.total_latency_ms,
                )
            )
        fact_count = sum(item.fact_claims for item in results)
        fact_hallucinations = sum(item.fact_hallucinations for item in results)
        citations = sum(item.citation_count for item in results)
        valid_citations = sum(item.valid_citations for item in results)
        cited_statements = sum(item.cited_statements for item in results)
        grounded_statements = sum(item.grounded_statements for item in results)
        latencies = sorted(item.latency_ms for item in results)
        return Stage6AgentReport(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            generated_at=datetime.now(UTC).isoformat(),
            corpus_product_count=dataset.corpus_product_count,
            case_count=len(results),
            task_completion_rate=_rate(item.task_complete for item in results),
            tool_selection_accuracy=_rate(item.tool_selection_correct for item in results),
            citation_precision=valid_citations / citations if citations else 1.0,
            citation_coverage=(grounded_statements / cited_statements if cited_statements else 1.0),
            structured_fact_claim_count=fact_count,
            structured_fact_hallucination_rate=(
                fact_hallucinations / fact_count if fact_count else 0.0
            ),
            condition_mutation_accuracy=_rate(item.condition_correct for item in results),
            average_tool_calls=fmean(item.tool_count for item in results),
            maximum_tool_calls=max((item.tool_count for item in results), default=0),
            invalid_loop_rate=invalid_loops / len(results) if results else 0.0,
            latency_p50_ms=_percentile(latencies, 0.50),
            latency_p95_ms=_percentile(latencies, 0.95),
            limitations=[
                "The corpus contains only 24 synthetic CC0 fixture products.",
                "The deterministic agent provider proves schemas and control flow, "
                "not LLM quality.",
                "Product prompt injection and model timeouts are covered by "
                "adversarial unit tests.",
            ],
            cases=results,
        )


def write_stage6_reports(report: Stage6AgentReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stage6-agent-evidence.json"
    markdown_path = output_dir / "stage6-agent-evidence.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def _fact_accuracy(response: AssistantResponse) -> tuple[int, int]:
    evidence = {
        (item.product_id, item.field): item
        for item in response.evidence
        if item.kind == "product_fact"
    }
    fields = (
        "title",
        "brand",
        "category",
        "price_amount",
        "currency",
        "wireless",
        "anc",
        "battery_hours",
        "weight_grams",
        "colors",
        "codecs",
        "water_resistance",
    )
    claims = 0
    hallucinations = 0
    for recommendation in response.recommendations:
        product = recommendation.product
        dumped = product.model_dump(mode="json")
        for field in fields:
            claims += 1
            item = evidence.get((product.id, field))
            expected = _normalized(dumped.get(field))
            if item is None or _normalized(item.value) != expected:
                hallucinations += 1
    return claims, hallucinations


def _citation_accuracy(response: AssistantResponse) -> tuple[int, int, int, int]:
    evidence = {item.id: item for item in response.evidence}
    statements = [
        statement
        for recommendation in response.recommendations
        for statement in [
            *recommendation.matched_requirements,
            *recommendation.reasons,
            *recommendation.tradeoffs,
        ]
    ]
    citations = [
        (recommendation.product.id, evidence_id)
        for recommendation in response.recommendations
        for evidence_id in recommendation.evidence_ids
    ]
    valid = sum(
        evidence_id in evidence and evidence[evidence_id].product_id == product_id
        for product_id, evidence_id in citations
    )
    grounded = sum(bool(statement.evidence_ids) for statement in statements)
    return len(statements), grounded, len(citations), valid


def _normalized(value: object) -> object:
    if value is None or isinstance(value, (bool, list)):
        return value
    return str(value)


def _rate(values: Any) -> float:
    materialized = list(values)
    return sum(bool(value) for value in materialized) / len(materialized) if materialized else 1.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    index = max(0, math.ceil(len(values) * percentile) - 1)
    return values[index]


def _markdown(report: Stage6AgentReport) -> str:
    lines = [
        "# Stage 6 bounded-agent and evidence evaluation",
        "",
        f"- Dataset: `{report.dataset_name}` / `{report.dataset_version}`",
        f"- Corpus: {report.corpus_product_count} synthetic CC0 fixtures",
        f"- Cases: {report.case_count}",
        f"- Generated: `{report.generated_at}`",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Task completion | {report.task_completion_rate:.4f} |",
        f"| Tool selection accuracy | {report.tool_selection_accuracy:.4f} |",
        f"| Citation precision | {report.citation_precision:.4f} |",
        f"| Citation coverage | {report.citation_coverage:.4f} |",
        f"| Structured fact claims | {report.structured_fact_claim_count} |",
        f"| Structured fact hallucination rate | {report.structured_fact_hallucination_rate:.4f} |",
        f"| Condition mutation accuracy | {report.condition_mutation_accuracy:.4f} |",
        f"| Average tool calls | {report.average_tool_calls:.3f} |",
        f"| Maximum tool calls | {report.maximum_tool_calls} |",
        f"| Invalid loop rate | {report.invalid_loop_rate:.4f} |",
        f"| Full answer P50 ms | {report.latency_p50_ms:.3f} |",
        f"| Full answer P95 ms | {report.latency_p95_ms:.3f} |",
        "",
        "## Per-case results",
        "",
        "| ID | Conversation | Status | Task | Conditions | Tools | Facts | "
        "Hallucinations | Degraded |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in report.cases:
        lines.append(
            f"| {item.id} | {item.conversation_id} | {item.status} | "
            f"{int(item.task_complete)} | {int(item.condition_correct)} | "
            f"{int(item.tool_selection_correct)} | {item.fact_claims} | "
            f"{item.fact_hallucinations} | {', '.join(item.degraded_reasons) or '-'} |"
        )
    lines.extend(["", "## Limitations", "", *[f"- {item}" for item in report.limitations]])
    return "\n".join(lines) + "\n"
