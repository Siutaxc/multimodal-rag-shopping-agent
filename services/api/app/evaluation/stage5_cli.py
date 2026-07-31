"""CLI for pure-image and image/text rank-fusion ablation."""

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.images import ImageSearchRepository
from app.db.search import DenseSearchRepository, LexicalSearchRepository
from app.db.session import get_engine
from app.evaluation.stage5_runner import Stage5EvaluationRunner, write_stage5_reports
from app.evaluation.stage5_schemas import Stage5Dataset
from app.providers.images import create_image_embedding_provider
from app.providers.retrieval import create_embedding_provider, create_reranker_provider
from app.providers.storage import LocalObjectStorage
from app.retrieval.hybrid import HybridSearchService

_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the stage-five multimodal ablation")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_WORKSPACE_ROOT / "evals/datasets/stage5_multimodal_queries.json",
    )
    parser.add_argument("--output-dir", type=Path, default=_WORKSPACE_ROOT / "evals/reports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dataset = Stage5Dataset.model_validate_json(args.dataset.resolve().read_text(encoding="utf-8"))
    settings = Settings()
    image_provider = create_image_embedding_provider(settings)
    with Session(get_engine(str(settings.database_url))) as session:
        text_service = HybridSearchService(
            LexicalSearchRepository(session),
            DenseSearchRepository(session),
            create_embedding_provider(settings),
            create_reranker_provider(settings),
            settings,
        )
        report = Stage5EvaluationRunner(
            session,
            ImageSearchRepository(session),
            image_provider,
            LocalObjectStorage(settings.object_storage_path),
            text_service,
            image_candidate_k=settings.image_candidate_k,
            fusion_candidate_k=settings.fusion_candidate_k,
            rrf_k=settings.rrf_k,
            text_weight=settings.multimodal_text_weight,
            image_weight=settings.multimodal_image_weight,
        ).run(dataset)
    json_path, markdown_path = write_stage5_reports(report, args.output_dir.resolve())
    print(
        json.dumps(
            {
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
