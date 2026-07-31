"""Run the lexical baseline against PostgreSQL and serialize an auditable report."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from typing import Any

from app.api.search import SearchFiltersInput
from app.db.models import Product
from app.db.products import ProductFilters
from app.db.search import LexicalSearchRepository
from app.evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank
from app.evaluation.schemas import EvaluationDataset
from app.retrieval.documents import LEXICAL_DOCUMENT_VERSION


@dataclass(frozen=True)
class QueryEvaluation:
    """Per-query evidence retained in both report formats."""

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


@dataclass(frozen=True)
class EvaluationReport:
    """Aggregate baseline plus its complete per-query trace."""

    dataset_name: str
    dataset_version: str
    search_document_version: str
    generated_at: str
    corpus_product_count: int
    limitations: list[str]
    query_count: int
    judged_query_count: int
    empty_expected_query_count: int
    recall_at_5: float
    recall_at_10: float
    precision_at_5: float
    ndcg_at_10: float
    mrr: float
    hard_condition_violation_rate: float
    empty_result_accuracy: float
    queries: list[QueryEvaluation]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LexicalEvaluationRunner:
    """Evaluate the same repository used by the HTTP endpoint."""

    def __init__(self, repository: LexicalSearchRepository) -> None:
        self._repository = repository

    def run(self, dataset: EvaluationDataset) -> EvaluationReport:
        query_results: list[QueryEvaluation] = []
        total_returned = 0
        total_violations = 0
        empty_correct = 0

        for evaluation_query in dataset.queries:
            filters = _repository_filters(evaluation_query.filters)
            hits, _ = self._repository.search(evaluation_query.query, filters)
            retrieved = [hit.product.source_id for hit in hits]
            relevant = set(evaluation_query.relevance)
            violations = sum(
                _violates_hard_filters(hit.product, evaluation_query.filters) for hit in hits
            )
            total_returned += len(hits)
            total_violations += violations
            if not relevant and not hits:
                empty_correct += 1

            query_results.append(
                QueryEvaluation(
                    id=evaluation_query.id,
                    query=evaluation_query.query,
                    expected_source_ids=sorted(relevant),
                    retrieved_source_ids=retrieved,
                    recall_at_5=recall_at_k(retrieved, relevant, 5) if relevant else None,
                    recall_at_10=recall_at_k(retrieved, relevant, 10) if relevant else None,
                    precision_at_5=precision_at_k(retrieved, relevant, 5) if relevant else None,
                    ndcg_at_10=(
                        ndcg_at_k(retrieved, evaluation_query.relevance, 10) if relevant else None
                    ),
                    reciprocal_rank=reciprocal_rank(retrieved, relevant) if relevant else None,
                    hard_filter_violations=violations,
                )
            )

        judged = [result for result in query_results if result.recall_at_10 is not None]
        empty_count = len(query_results) - len(judged)
        return EvaluationReport(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            search_document_version=LEXICAL_DOCUMENT_VERSION,
            generated_at=datetime.now(UTC).isoformat(),
            corpus_product_count=dataset.corpus_product_count,
            limitations=[
                "The corpus contains only 24 synthetic CC0 fixtures.",
                "Queries were authored for deterministic engineering regression, "
                "not production quality claims.",
                "PostgreSQL simple FTS has no general Chinese word segmentation; "
                "documents expose explicit fact aliases and observed scene terms.",
            ],
            query_count=len(query_results),
            judged_query_count=len(judged),
            empty_expected_query_count=empty_count,
            recall_at_5=_mean_metric(judged, "recall_at_5"),
            recall_at_10=_mean_metric(judged, "recall_at_10"),
            precision_at_5=_mean_metric(judged, "precision_at_5"),
            ndcg_at_10=_mean_metric(judged, "ndcg_at_10"),
            mrr=_mean_metric(judged, "reciprocal_rank"),
            hard_condition_violation_rate=(
                total_violations / total_returned if total_returned else 0.0
            ),
            empty_result_accuracy=empty_correct / empty_count if empty_count else 1.0,
            queries=query_results,
        )


def write_reports(report: EvaluationReport, output_dir: Path) -> tuple[Path, Path]:
    """Write machine-readable JSON and a concise human-readable Markdown baseline."""

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stage3-lexical-baseline.json"
    markdown_path = output_dir / "stage3-lexical-baseline.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    return json_path, markdown_path


def _repository_filters(filters: SearchFiltersInput) -> ProductFilters:
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
        color=filters.color,
        codec=filters.codec,
    )


def _violates_hard_filters(product: Product, filters: SearchFiltersInput) -> bool:
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
    if filters.color is not None:
        colors = {color.casefold() for color in product.colors}
        if filters.color.strip().casefold() not in colors:
            return True
    if filters.codec is not None:
        codecs = {codec.upper() for codec in product.codecs}
        if filters.codec.strip().upper() not in codecs:
            return True
    return False


def _mean_metric(results: list[QueryEvaluation], field: str) -> float:
    values = [getattr(result, field) for result in results]
    numeric_values = [value for value in values if isinstance(value, float)]
    return fmean(numeric_values) if numeric_values else 0.0


def _markdown_report(report: EvaluationReport) -> str:
    lines = [
        "# Stage 3 lexical baseline",
        "",
        f"- Dataset: `{report.dataset_name}` / `{report.dataset_version}`",
        f"- Search document: `{report.search_document_version}`",
        f"- Corpus: {report.corpus_product_count} synthetic CC0 fixture products",
        f"- Generated: `{report.generated_at}`",
        f"- Queries: {report.query_count} ({report.judged_query_count} judged, "
        f"{report.empty_expected_query_count} empty-result)",
        f"- Recall@5: {report.recall_at_5:.4f}",
        f"- Recall@10: {report.recall_at_10:.4f}",
        f"- Precision@5: {report.precision_at_5:.4f}",
        f"- nDCG@10: {report.ndcg_at_10:.4f}",
        f"- MRR: {report.mrr:.4f}",
        f"- Hard-condition violation rate: {report.hard_condition_violation_rate:.4f}",
        f"- Empty-result accuracy: {report.empty_result_accuracy:.4f}",
        "",
        "## Limitations",
        "",
        *[f"- {limitation}" for limitation in report.limitations],
        "",
        "## Query trace",
        "",
        "| ID | Query | Expected | Retrieved | R@10 | nDCG@10 | Violations |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for item in report.queries:
        recall = "n/a" if item.recall_at_10 is None else f"{item.recall_at_10:.3f}"
        ndcg = "n/a" if item.ndcg_at_10 is None else f"{item.ndcg_at_10:.3f}"
        lines.append(
            f"| {item.id} | {item.query} | {', '.join(item.expected_source_ids) or '∅'} | "
            f"{', '.join(item.retrieved_source_ids) or '∅'} | {recall} | {ndcg} | "
            f"{item.hard_filter_violations} |"
        )
    return "\n".join(lines) + "\n"
