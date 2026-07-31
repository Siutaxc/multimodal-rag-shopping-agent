"""Four-way text retrieval ablation with complete per-query evidence."""

import json
import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from typing import Any, Protocol

from app.api.search import SearchFiltersInput
from app.db.models import Product
from app.db.products import ProductFilters
from app.evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank
from app.retrieval.hybrid import HybridSearchService, SearchMode


class EvaluationQueryLike(Protocol):
    id: str
    query: str
    relevance: dict[str, int]
    filters: SearchFiltersInput


@dataclass(frozen=True)
class ModeQueryResult:
    id: str
    query: str
    expected_source_ids: list[str]
    retrieved_source_ids: list[str]
    recall_at_5: float | None
    recall_at_10: float | None
    precision_at_5: float | None
    ndcg_at_10: float | None
    reciprocal_rank: float | None
    hard_filter_violations: int
    latency_ms: float
    actual_mode: str
    degraded_reason: str | None


@dataclass(frozen=True)
class ModeReport:
    mode: str
    recall_at_5: float
    recall_at_10: float
    precision_at_5: float
    ndcg_at_10: float
    mrr: float
    hard_condition_violation_rate: float
    empty_result_accuracy: float
    latency_p50_ms: float
    latency_p95_ms: float
    failure_query_ids: list[str]
    queries: list[ModeQueryResult]


@dataclass(frozen=True)
class Stage4AblationReport:
    dataset_name: str
    dataset_version: str
    generated_at: str
    corpus_product_count: int
    query_count: int
    frozen_lexical_query_count: int
    semantic_query_count: int
    parameters: dict[str, int]
    models: dict[str, str]
    limitations: list[str]
    modes: list[ModeReport]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Stage4EvaluationRunner:
    def __init__(self, service: HybridSearchService) -> None:
        self._service = service

    def run(
        self,
        *,
        dataset_name: str,
        dataset_version: str,
        corpus_product_count: int,
        frozen_queries: Sequence[EvaluationQueryLike],
        semantic_queries: Sequence[EvaluationQueryLike],
        parameters: dict[str, int],
        models: dict[str, str],
    ) -> Stage4AblationReport:
        queries = [*frozen_queries, *semantic_queries]
        reports = [self._run_mode(mode, queries) for mode in SearchMode]
        return Stage4AblationReport(
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            generated_at=datetime.now(UTC).isoformat(),
            corpus_product_count=corpus_product_count,
            query_count=len(queries),
            frozen_lexical_query_count=len(frozen_queries),
            semantic_query_count=len(semantic_queries),
            parameters=parameters,
            models=models,
            limitations=[
                "The corpus contains only 24 synthetic CC0 fixture products.",
                "The deterministic offline providers validate retrieval plumbing, "
                "not BGE production quality.",
                "All failures are retained; metrics must not be generalized to "
                "open-domain shopping search.",
            ],
            modes=reports,
        )

    def _run_mode(self, mode: SearchMode, queries: Sequence[EvaluationQueryLike]) -> ModeReport:
        results: list[ModeQueryResult] = []
        total_returned = 0
        violations_total = 0
        empty_correct = 0
        for item in queries:
            execution = self._service.search(item.query, _filters(item.filters), mode=mode)
            candidates = execution.items[:10]
            retrieved = [candidate.product.source_id for candidate in candidates]
            relevant = set(item.relevance)
            violations = sum(_violates(candidate.product, item.filters) for candidate in candidates)
            total_returned += len(candidates)
            violations_total += violations
            if not relevant and not candidates:
                empty_correct += 1
            latency = execution.trace.get("latency_ms", {})
            latency_ms = float(latency.get("total", 0.0)) if isinstance(latency, dict) else 0.0
            degraded = execution.trace.get("degraded_reason")
            results.append(
                ModeQueryResult(
                    id=item.id,
                    query=item.query,
                    expected_source_ids=sorted(relevant),
                    retrieved_source_ids=retrieved,
                    recall_at_5=recall_at_k(retrieved, relevant, 5) if relevant else None,
                    recall_at_10=recall_at_k(retrieved, relevant, 10) if relevant else None,
                    precision_at_5=precision_at_k(retrieved, relevant, 5) if relevant else None,
                    ndcg_at_10=ndcg_at_k(retrieved, item.relevance, 10) if relevant else None,
                    reciprocal_rank=reciprocal_rank(retrieved, relevant) if relevant else None,
                    hard_filter_violations=violations,
                    latency_ms=latency_ms,
                    actual_mode=execution.mode,
                    degraded_reason=degraded if isinstance(degraded, str) else None,
                )
            )
        judged = [result for result in results if result.recall_at_10 is not None]
        empty_count = len(results) - len(judged)
        latencies = sorted(result.latency_ms for result in results)
        return ModeReport(
            mode=mode.value,
            recall_at_5=_mean(judged, "recall_at_5"),
            recall_at_10=_mean(judged, "recall_at_10"),
            precision_at_5=_mean(judged, "precision_at_5"),
            ndcg_at_10=_mean(judged, "ndcg_at_10"),
            mrr=_mean(judged, "reciprocal_rank"),
            hard_condition_violation_rate=(
                violations_total / total_returned if total_returned else 0.0
            ),
            empty_result_accuracy=empty_correct / empty_count if empty_count else 1.0,
            latency_p50_ms=_percentile(latencies, 0.50),
            latency_p95_ms=_percentile(latencies, 0.95),
            failure_query_ids=[
                result.id
                for result in results
                if (result.recall_at_10 is not None and result.recall_at_10 < 1.0)
                or (result.ndcg_at_10 is not None and result.ndcg_at_10 < 1.0)
                or result.hard_filter_violations > 0
            ],
            queries=results,
        )


def write_stage4_reports(
    report: Stage4AblationReport,
    output_dir: Path,
    *,
    basename: str = "stage4-text-ablation",
    title: str = "Stage 4 text retrieval ablation",
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{basename}.json"
    markdown_path = output_dir / f"{basename}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(_markdown(report, title=title), encoding="utf-8")
    return json_path, markdown_path


def _markdown(
    report: Stage4AblationReport, *, title: str = "Stage 4 text retrieval ablation"
) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Dataset: `{report.dataset_name}` / `{report.dataset_version}`",
        f"- Corpus: {report.corpus_product_count} synthetic CC0 fixtures",
        f"- Queries: {report.query_count} "
        f"({report.frozen_lexical_query_count} frozen lexical + "
        f"{report.semantic_query_count} semantic)",
        f"- Generated: `{report.generated_at}`",
        f"- Models: `{report.models}`",
        f"- Parameters: `{report.parameters}`",
        "",
        "| Mode | R@5 | R@10 | P@5 | nDCG@10 | MRR | Hard violations | "
        "Empty accuracy | P50 ms | P95 ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in report.modes:
        lines.append(
            f"| {mode.mode} | {mode.recall_at_5:.4f} | {mode.recall_at_10:.4f} | "
            f"{mode.precision_at_5:.4f} | {mode.ndcg_at_10:.4f} | {mode.mrr:.4f} | "
            f"{mode.hard_condition_violation_rate:.4f} | {mode.empty_result_accuracy:.4f} | "
            f"{mode.latency_p50_ms:.3f} | {mode.latency_p95_ms:.3f} |"
        )
    lines.extend(["", "## Failure analysis", ""])
    for mode in report.modes:
        failures = ", ".join(mode.failure_query_ids) or "none"
        lines.append(f"- **{mode.mode}**: {failures}")
    lines.extend(["", "## Limitations", "", *[f"- {item}" for item in report.limitations]])
    lines.extend(["", "## Complete query trace", ""])
    for mode in report.modes:
        lines.extend(
            [
                f"### {mode.mode}",
                "",
                "| ID | Query | Expected | Retrieved | R@10 | nDCG@10 | Violations | Degraded |",
                "|---|---|---|---|---:|---:|---:|---|",
            ]
        )
        for item in mode.queries:
            recall = "n/a" if item.recall_at_10 is None else f"{item.recall_at_10:.3f}"
            ndcg = "n/a" if item.ndcg_at_10 is None else f"{item.ndcg_at_10:.3f}"
            lines.append(
                f"| {item.id} | {item.query} | {', '.join(item.expected_source_ids) or '∅'} | "
                f"{', '.join(item.retrieved_source_ids) or '∅'} | {recall} | {ndcg} | "
                f"{item.hard_filter_violations} | {item.degraded_reason or '—'} |"
            )
        lines.append("")
    return "\n".join(lines)


def _filters(filters: SearchFiltersInput) -> ProductFilters:
    return ProductFilters(
        page=1,
        page_size=10,
        category=filters.category,
        brand=filters.brand,
        price_min=filters.price_min,
        price_max=filters.price_max,
        currency=filters.currency,
        wireless=filters.wireless,
        anc=filters.anc,
        battery_hours_min=filters.battery_hours_min,
        weight_grams_max=filters.weight_grams_max,
        color=filters.color,
        codec=filters.codec,
        water_resistance=filters.water_resistance,
    )


def _violates(product: Product, filters: SearchFiltersInput) -> bool:
    if filters.category is not None and product.category != filters.category:
        return True
    if filters.brand is not None and product.brand.casefold() != filters.brand.strip().casefold():
        return True
    if filters.price_min is not None and product.price_amount < filters.price_min:
        return True
    if filters.price_max is not None and product.price_amount > filters.price_max:
        return True
    if filters.currency is not None and product.currency != filters.currency.upper():
        return True
    if filters.wireless is not None and product.wireless is not filters.wireless:
        return True
    if filters.anc is not None and product.anc is not filters.anc:
        return True
    if filters.battery_hours_min is not None and (
        product.battery_hours is None or product.battery_hours < filters.battery_hours_min
    ):
        return True
    if filters.weight_grams_max is not None and (
        product.weight_grams is None or product.weight_grams > filters.weight_grams_max
    ):
        return True
    if filters.color is not None and filters.color.casefold() not in {
        color.casefold() for color in product.colors
    }:
        return True
    if filters.codec is not None and filters.codec.upper() not in {
        codec.upper() for codec in product.codecs
    }:
        return True
    return bool(
        filters.water_resistance is not None
        and (
            product.water_resistance is None
            or product.water_resistance.upper() != filters.water_resistance.upper()
        )
    )


def _mean(results: list[ModeQueryResult], field: str) -> float:
    values = [getattr(result, field) for result in results]
    numeric = [value for value in values if isinstance(value, float)]
    return fmean(numeric) if numeric else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    index = max(0, math.ceil(len(values) * percentile) - 1)
    return values[index]
