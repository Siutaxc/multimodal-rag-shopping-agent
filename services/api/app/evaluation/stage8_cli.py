"""Run the 150-query stage-eight four-way text retrieval ablation."""

import argparse
import json
from dataclasses import replace
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.search import DenseSearchRepository, LexicalSearchRepository
from app.db.session import get_engine
from app.evaluation.schemas import EvaluationDataset
from app.evaluation.stage4_runner import Stage4EvaluationRunner, write_stage4_reports
from app.evaluation.stage4_schemas import Stage4DatasetExtension
from app.evaluation.stage8_schemas import Stage8DatasetExtension
from app.providers.retrieval import create_embedding_provider, create_reranker_provider
from app.retrieval.hybrid import HybridSearchService

_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the 150-query stage-eight ablation")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_WORKSPACE_ROOT / "evals/datasets/stage8_text_queries.json",
    )
    parser.add_argument("--output-dir", type=Path, default=_WORKSPACE_ROOT / "evals/reports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dataset = Stage8DatasetExtension.model_validate_json(
        args.dataset.resolve().read_text(encoding="utf-8")
    )
    lexical = EvaluationDataset.model_validate_json(
        (_WORKSPACE_ROOT / dataset.frozen_lexical_dataset).read_text(encoding="utf-8")
    )
    semantic = Stage4DatasetExtension.model_validate_json(
        (_WORKSPACE_ROOT / dataset.frozen_semantic_dataset).read_text(encoding="utf-8")
    )
    settings = Settings()
    embedding = create_embedding_provider(settings)
    reranker = create_reranker_provider(settings)
    with Session(
        get_engine(str(settings.database_url), settings.slow_query_threshold_ms)
    ) as session:
        service = HybridSearchService(
            LexicalSearchRepository(session),
            DenseSearchRepository(session),
            embedding,
            reranker,
            settings,
        )
        report = Stage4EvaluationRunner(service).run(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            corpus_product_count=dataset.corpus_product_count,
            frozen_queries=lexical.queries,
            semantic_queries=[*semantic.semantic_queries, *dataset.queries],
            parameters={
                "lexical_candidate_k": settings.lexical_candidate_k,
                "dense_candidate_k": settings.dense_candidate_k,
                "fusion_candidate_k": settings.fusion_candidate_k,
                "rerank_top_k": settings.rerank_top_k,
                "rrf_k": settings.rrf_k,
            },
            models={
                "embedding": embedding.identity.version_key,
                "reranker": reranker.identity.version_key,
            },
        )
    report = replace(
        report,
        limitations=[
            "The 150 queries target only 24 synthetic CC0 fixture products.",
            "The expanded exact, adversarial, and scenario cohorts are engineering regression "
            "data, not an independent production relevance judgment set.",
            "Deterministic fixture providers prove reproducibility and failure handling, not "
            "real BGE-M3 or reranker quality.",
            "Every failed query remains in the JSON and Markdown reports.",
        ],
    )
    if report.query_count < 150:
        raise RuntimeError("stage-eight evaluation must contain at least 150 queries")
    json_path, markdown_path = write_stage4_reports(
        report,
        args.output_dir.resolve(),
        basename="stage8-text-ablation",
        title="Stage 8 expanded text retrieval ablation",
    )
    print(
        json.dumps(
            {
                "query_count": report.query_count,
                "failure_counts": {mode.mode: len(mode.failure_query_ids) for mode in report.modes},
                "json_report": str(json_path),
                "markdown_report": str(markdown_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
