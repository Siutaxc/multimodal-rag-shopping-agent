"""CLI for stage-six bounded-agent and evidence evaluation."""

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.agent.service import BoundedShoppingAgent
from app.agent.state import MemoryAgentStateStore
from app.agent.tools import ShoppingAgentTools
from app.core.settings import Settings
from app.db.images import ImageSearchRepository, UploadedImageAssetRepository
from app.db.products import ProductRepository
from app.db.search import DenseSearchRepository, LexicalSearchRepository
from app.db.session import get_engine
from app.evaluation.stage6_runner import Stage6EvaluationRunner, write_stage6_reports
from app.evaluation.stage6_schemas import Stage6Dataset
from app.images.search import MultimodalSearchService
from app.providers.agent import create_agent_model_provider
from app.providers.images import create_image_embedding_provider
from app.providers.retrieval import create_embedding_provider, create_reranker_provider
from app.providers.storage import LocalObjectStorage
from app.retrieval.hybrid import HybridSearchService

_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run stage-six agent evidence evaluation")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_WORKSPACE_ROOT / "evals/datasets/stage6_agent_cases.json",
    )
    parser.add_argument("--output-dir", type=Path, default=_WORKSPACE_ROOT / "evals/reports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dataset = Stage6Dataset.model_validate_json(args.dataset.resolve().read_text(encoding="utf-8"))
    settings = Settings()
    with Session(get_engine(str(settings.database_url))) as session:
        text_search = HybridSearchService(
            LexicalSearchRepository(session),
            DenseSearchRepository(session),
            create_embedding_provider(settings),
            create_reranker_provider(settings),
            settings,
        )
        multimodal_search = MultimodalSearchService(
            UploadedImageAssetRepository(session),
            ImageSearchRepository(session),
            text_search,
            create_image_embedding_provider(settings),
            LocalObjectStorage(settings.object_storage_path),
            settings,
        )
        agent = BoundedShoppingAgent(
            ShoppingAgentTools(ProductRepository(session), text_search, multimodal_search),
            MemoryAgentStateStore(),
            create_agent_model_provider(settings),
            settings,
        )
        report = Stage6EvaluationRunner(agent).run(dataset)
    json_path, markdown_path = write_stage6_reports(report, args.output_dir.resolve())
    print(
        json.dumps(
            {
                "case_count": report.case_count,
                "structured_fact_claim_count": report.structured_fact_claim_count,
                "structured_fact_hallucination_rate": (report.structured_fact_hallucination_rate),
                "citation_precision": report.citation_precision,
                "maximum_tool_calls": report.maximum_tool_calls,
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
