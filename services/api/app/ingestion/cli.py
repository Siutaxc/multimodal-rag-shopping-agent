"""Command-line entry point for deterministic fixture ingestion."""

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.session import get_engine
from app.ingestion.service import IngestionService, load_fixture
from app.providers.storage import LocalObjectStorage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a ShopLens product fixture")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("data/fixtures/headphones.json"),
        help="UTF-8 fixture JSON path",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    fixture_path: Path = args.fixture.resolve()
    settings = Settings()
    payload = load_fixture(fixture_path)
    storage = LocalObjectStorage(settings.object_storage_path)
    with Session(get_engine(str(settings.database_url))) as session:
        report = IngestionService(session, storage).import_payload(
            payload, fixture_root=fixture_path.parent
        )
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
