"""CLI for deterministic or HTTP-backed product image vector materialization."""

import json
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.session import get_engine
from app.images.indexing import ImageEmbeddingIndexer
from app.providers.images import create_image_embedding_provider
from app.providers.storage import LocalObjectStorage


def main() -> int:
    settings = Settings()
    with Session(get_engine(str(settings.database_url))) as session:
        report = ImageEmbeddingIndexer(
            session,
            create_image_embedding_provider(settings),
            LocalObjectStorage(settings.object_storage_path),
            batch_size=settings.image_embedding_batch_size,
        ).run()
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
