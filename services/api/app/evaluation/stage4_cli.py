"""CLI for the stage-four lexical/dense/RRF/rerank ablation."""

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.search import DenseSearchRepository, LexicalSearchRepository
from app.db.session import get_engine
from app.evaluation.schemas import EvaluationDataset
from app.evaluation.stage4_runner import Stage4EvaluationRunner, write_stage4_reports
from app.evaluation.stage4_schemas import Stage4DatasetExtension
from app.providers.retrieval import create_embedding_provider, create_reranker_provider
from app.retrieval.hybrid import HybridSearchService

_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the stage-four text retrieval ablation")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_WORKSPACE_ROOT / "evals/datasets/stage4_text_queries.json",
    )
    parser.add_argument("--output-dir", type=Path, default=_WORKSPACE_ROOT / "evals/reports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    extension_path: Path = args.dataset.resolve()
    extension = Stage4DatasetExtension.model_validate_json(
        extension_path.read_text(encoding="utf-8")
    )
    base_path = (_WORKSPACE_ROOT / extension.base_dataset).resolve()
    base = EvaluationDataset.model_validate_json(base_path.read_text(encoding="utf-8"))
    settings = Settings()
    embedding = create_embedding_provider(settings)
    reranker = create_reranker_provider(settings)
    with Session(get_engine(str(settings.database_url))) as session:
        service = HybridSearchService(
            LexicalSearchRepository(session),
            DenseSearchRepository(session),
            embedding,
            reranker,
            settings,
        )
        report = Stage4EvaluationRunner(service).run(
            dataset_name=extension.name,
            dataset_version=extension.version,
            corpus_product_count=extension.corpus_product_count,
            frozen_queries=base.queries,
            semantic_queries=extension.semantic_queries,
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
    json_path, markdown_path = write_stage4_reports(report, args.output_dir.resolve())
    print(
        json.dumps(
            {
                "query_count": report.query_count,
                "modes": {
                    mode.mode: {
                        "recall_at_10": mode.recall_at_10,
                        "ndcg_at_10": mode.ndcg_at_10,
                        "hard_condition_violation_rate": mode.hard_condition_violation_rate,
                    }
                    for mode in report.modes
                },
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
