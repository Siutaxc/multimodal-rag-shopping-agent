"""Stage-five image-channel and multimodal ablation with complete failure traces."""

import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from time import perf_counter
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.search import SearchFiltersInput
from app.db.images import ImageSearchRepository
from app.db.models import Product, ProductImage
from app.db.products import ProductFilters
from app.evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank
from app.evaluation.stage5_schemas import Stage5Dataset, Stage5EvaluationQuery
from app.images.indexing import IMAGE_REPRESENTATION_VERSION
from app.images.search import multimodal_rank_fusion
from app.providers.images import ImageEmbeddingProvider
from app.providers.storage import ObjectStorage
from app.retrieval.hybrid import HybridSearchService, SearchMode

Stage5Mode = Literal["pure_image", "mixed_image_only", "mixed_text_only", "mixed_full"]


@dataclass(frozen=True)
class Stage5QueryResult:
    id: str
    reference_source_id: str
    query: str | None
    expected_source_ids: list[str]
    retrieved_source_ids: list[str]
    recall_at_5: float | None
    recall_at_10: float | None
    precision_at_5: float | None
    ndcg_at_10: float | None
    reciprocal_rank: float | None
    hard_filter_violations: int
    latency_ms: float


@dataclass(frozen=True)
class Stage5ModeReport:
    mode: Stage5Mode
    query_count: int
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
    queries: list[Stage5QueryResult]


@dataclass(frozen=True)
class Stage5AblationReport:
    dataset_name: str
    dataset_version: str
    generated_at: str
    corpus_product_count: int
    pure_image_query_count: int
    multimodal_query_count: int
    parameters: dict[str, float | int]
    models: dict[str, str]
    limitations: list[str]
    modes: list[Stage5ModeReport]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Stage5EvaluationRunner:
    def __init__(
        self,
        session: Session,
        image_repository: ImageSearchRepository,
        image_provider: ImageEmbeddingProvider,
        storage: ObjectStorage,
        text_service: HybridSearchService,
        *,
        image_candidate_k: int,
        fusion_candidate_k: int,
        rrf_k: int,
        text_weight: float,
        image_weight: float,
    ) -> None:
        self._session = session
        self._images = image_repository
        self._provider = image_provider
        self._storage = storage
        self._text = text_service
        self._image_candidate_k = image_candidate_k
        self._fusion_candidate_k = fusion_candidate_k
        self._rrf_k = rrf_k
        self._text_weight = text_weight
        self._image_weight = image_weight

    def run(self, dataset: Stage5Dataset) -> Stage5AblationReport:
        pure = [query for query in dataset.queries if query.kind == "pure_image"]
        mixed = [query for query in dataset.queries if query.kind == "multimodal"]
        modes: list[Stage5ModeReport] = [
            self._run_mode("pure_image", pure),
            self._run_mode("mixed_image_only", mixed),
            self._run_mode("mixed_text_only", mixed),
            self._run_mode("mixed_full", mixed),
        ]
        return Stage5AblationReport(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            generated_at=datetime.now(UTC).isoformat(),
            corpus_product_count=dataset.corpus_product_count,
            pure_image_query_count=len(pure),
            multimodal_query_count=len(mixed),
            parameters={
                "image_candidate_k": self._image_candidate_k,
                "fusion_candidate_k": self._fusion_candidate_k,
                "rrf_k": self._rrf_k,
                "text_weight": self._text_weight,
                "image_weight": self._image_weight,
            },
            models={"image_embedding": self._provider.identity.version_key},
            limitations=[
                "The corpus contains only 24 synthetic CC0 products and synthetic artwork.",
                "The deterministic pixel provider validates engineering behavior, "
                "not SigLIP2 quality.",
                "Reference images are checked-in product artwork; open-domain photos "
                "are not measured.",
                "All annotated failures are retained and cannot be generalized to "
                "production traffic.",
            ],
            modes=modes,
        )

    def _run_mode(self, mode: Stage5Mode, queries: list[Stage5EvaluationQuery]) -> Stage5ModeReport:
        results: list[Stage5QueryResult] = []
        total_returned = violations_total = empty_correct = 0
        for item in queries:
            started = perf_counter()
            filters = _filters(item.filters)
            image_hits = self._image_hits(item.reference_source_id, filters)
            if mode in {"pure_image", "mixed_image_only"}:
                products = [hit.product for hit in image_hits[:10]]
            else:
                assert item.query is not None
                text = self._text.search(item.query, filters, mode=SearchMode.RERANK)
                if mode == "mixed_text_only":
                    products = [candidate.product for candidate in text.items[:10]]
                else:
                    fused = multimodal_rank_fusion(
                        text.items,
                        image_hits,
                        rrf_k=self._rrf_k,
                        text_weight=self._text_weight,
                        image_weight=self._image_weight,
                        limit=self._fusion_candidate_k,
                    )
                    products = [candidate.product for candidate in fused[:10]]
            retrieved = [product.source_id for product in products]
            relevant = set(item.relevance)
            violations = sum(_violates(product, item.filters) for product in products)
            total_returned += len(products)
            violations_total += violations
            if not relevant and not products:
                empty_correct += 1
            results.append(
                Stage5QueryResult(
                    id=item.id,
                    reference_source_id=item.reference_source_id,
                    query=item.query,
                    expected_source_ids=sorted(relevant),
                    retrieved_source_ids=retrieved,
                    recall_at_5=recall_at_k(retrieved, relevant, 5) if relevant else None,
                    recall_at_10=recall_at_k(retrieved, relevant, 10) if relevant else None,
                    precision_at_5=precision_at_k(retrieved, relevant, 5) if relevant else None,
                    ndcg_at_10=ndcg_at_k(retrieved, item.relevance, 10) if relevant else None,
                    reciprocal_rank=reciprocal_rank(retrieved, relevant) if relevant else None,
                    hard_filter_violations=violations,
                    latency_ms=round((perf_counter() - started) * 1000, 3),
                )
            )
        judged = [result for result in results if result.recall_at_10 is not None]
        empty_count = len(results) - len(judged)
        latencies = sorted(result.latency_ms for result in results)
        return Stage5ModeReport(
            mode=mode,
            query_count=len(results),
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

    def _image_hits(self, source_id: str, filters: ProductFilters) -> list[Any]:
        image = self._session.scalar(
            select(ProductImage)
            .join(Product, Product.id == ProductImage.product_id)
            .where(Product.source_id == source_id)
            .order_by(ProductImage.position)
        )
        if image is None:
            raise ValueError(f"reference product has no image: {source_id}")
        vector = self._provider.embed_images(
            [self._storage.resolve(image.storage_key).read_bytes()]
        )[0]
        identity = self._provider.identity
        assert identity.dimension is not None
        hits, _ = self._images.search(
            vector,
            filters,
            model_name=identity.model_name,
            model_version=identity.model_version,
            dimension=identity.dimension,
            representation_version=IMAGE_REPRESENTATION_VERSION,
            limit=self._image_candidate_k,
        )
        return hits


def write_stage5_reports(report: Stage5AblationReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stage5-multimodal-ablation.json"
    markdown_path = output_dir / "stage5-multimodal-ablation.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def _markdown(report: Stage5AblationReport) -> str:
    lines = [
        "# Stage 5 multimodal retrieval ablation",
        "",
        f"- Dataset: `{report.dataset_name}` / `{report.dataset_version}`",
        f"- Corpus: {report.corpus_product_count} synthetic CC0 fixtures",
        f"- Queries: {report.pure_image_query_count} pure image + "
        f"{report.multimodal_query_count} multimodal",
        f"- Models: `{report.models}`",
        f"- Parameters: `{report.parameters}`",
        "",
        "| Mode | Queries | R@5 | R@10 | P@5 | nDCG@10 | MRR | Hard violations | "
        "Empty accuracy | P50 ms | P95 ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in report.modes:
        lines.append(
            f"| {mode.mode} | {mode.query_count} | {mode.recall_at_5:.4f} | "
            f"{mode.recall_at_10:.4f} | {mode.precision_at_5:.4f} | "
            f"{mode.ndcg_at_10:.4f} | {mode.mrr:.4f} | "
            f"{mode.hard_condition_violation_rate:.4f} | "
            f"{mode.empty_result_accuracy:.4f} | {mode.latency_p50_ms:.3f} | "
            f"{mode.latency_p95_ms:.3f} |"
        )
    lines.extend(["", "## Failure analysis", ""])
    for mode in report.modes:
        lines.append(f"- **{mode.mode}**: {', '.join(mode.failure_query_ids) or 'none'}")
    lines.extend(["", "## Limitations", "", *[f"- {item}" for item in report.limitations]])
    lines.extend(["", "## Complete query trace", ""])
    for mode in report.modes:
        lines.extend(
            [
                f"### {mode.mode}",
                "",
                "| ID | Reference | Text | Expected | Retrieved | R@10 | nDCG@10 | Violations |",
                "|---|---|---|---|---|---:|---:|---:|",
            ]
        )
        for item in mode.queries:
            recall = "n/a" if item.recall_at_10 is None else f"{item.recall_at_10:.3f}"
            ndcg = "n/a" if item.ndcg_at_10 is None else f"{item.ndcg_at_10:.3f}"
            lines.append(
                f"| {item.id} | {item.reference_source_id} | {item.query or '—'} | "
                f"{', '.join(item.expected_source_ids) or '∅'} | "
                f"{', '.join(item.retrieved_source_ids) or '∅'} | {recall} | {ndcg} | "
                f"{item.hard_filter_violations} |"
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
        color=filters.color,
        codec=filters.codec,
    )


def _violates(product: Product, filters: SearchFiltersInput) -> bool:
    checks = [
        filters.category is not None and product.category != filters.category,
        filters.brand is not None and product.brand.casefold() != filters.brand.strip().casefold(),
        filters.price_min is not None and product.price_amount < filters.price_min,
        filters.price_max is not None and product.price_amount > filters.price_max,
        filters.currency is not None and product.currency != filters.currency.upper(),
        filters.wireless is not None and product.wireless is not filters.wireless,
        filters.anc is not None and product.anc is not filters.anc,
        filters.battery_hours_min is not None
        and (product.battery_hours is None or product.battery_hours < filters.battery_hours_min),
        filters.color is not None
        and filters.color.casefold() not in {color.casefold() for color in product.colors},
        filters.codec is not None
        and filters.codec.upper() not in {codec.upper() for codec in product.codecs},
    ]
    return any(checks)


def _mean(results: list[Stage5QueryResult], field: str) -> float:
    values = [getattr(result, field) for result in results]
    numeric = [value for value in values if isinstance(value, float)]
    return fmean(numeric) if numeric else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    index = max(0, math.ceil(len(values) * percentile) - 1)
    return values[index]
