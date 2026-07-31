"""CLI for the checked-in PostgreSQL lexical baseline."""

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.search import LexicalSearchRepository
from app.db.session import get_engine
from app.evaluation.runner import LexicalEvaluationRunner, write_reports
from app.evaluation.schemas import EvaluationDataset

_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the stage-three lexical baseline")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_WORKSPACE_ROOT / "evals/datasets/stage3_lexical_queries.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_WORKSPACE_ROOT / "evals/reports",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dataset_path: Path = args.dataset.resolve()
    output_dir: Path = args.output_dir.resolve()
    dataset = EvaluationDataset.model_validate_json(dataset_path.read_text(encoding="utf-8"))
    settings = Settings()
    with Session(get_engine(str(settings.database_url))) as session:
        report = LexicalEvaluationRunner(LexicalSearchRepository(session)).run(dataset)
    json_path, markdown_path = write_reports(report, output_dir)
    print(
        json.dumps(
            {
                "query_count": report.query_count,
                "recall_at_10": report.recall_at_10,
                "ndcg_at_10": report.ndcg_at_10,
                "mrr": report.mrr,
                "hard_condition_violation_rate": report.hard_condition_violation_rate,
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
