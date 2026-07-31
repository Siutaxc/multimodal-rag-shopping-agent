"""CLI for deterministic or HTTP-backed text vector materialization."""

import json
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.session import get_engine
from app.providers.retrieval import create_embedding_provider
from app.retrieval.indexing import TextEmbeddingIndexer


def main() -> int:
    settings = Settings()
    provider = create_embedding_provider(settings)
    with Session(get_engine(str(settings.database_url))) as session:
        report = TextEmbeddingIndexer(
            session, provider, batch_size=settings.embedding_batch_size
        ).run()
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
