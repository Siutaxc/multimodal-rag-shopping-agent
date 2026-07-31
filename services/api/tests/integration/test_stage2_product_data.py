"""PostgreSQL migration, ingestion, text retrieval, evaluation, and HTTP tests."""

import os
from collections.abc import Sequence
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from app.core.settings import Settings
from app.db.images import ImageSearchRepository
from app.db.models import (
    ImageEmbedding,
    IngestionJob,
    Product,
    ProductDocument,
    ProductImage,
    TextEmbedding,
)
from app.db.products import ProductFilters, ProductRepository
from app.db.search import DenseSearchRepository, LexicalSearchRepository
from app.db.session import get_engine
from app.domain.products import IngestionStatus, ProductCategory
from app.evaluation.runner import LexicalEvaluationRunner
from app.evaluation.schemas import EvaluationDataset
from app.evaluation.stage4_runner import Stage4EvaluationRunner
from app.evaluation.stage4_schemas import Stage4DatasetExtension
from app.evaluation.stage5_runner import Stage5EvaluationRunner
from app.evaluation.stage5_schemas import Stage5Dataset
from app.images.indexing import IMAGE_REPRESENTATION_VERSION, ImageEmbeddingIndexer
from app.ingestion.service import IngestionService, load_fixture
from app.main import create_app
from app.providers.images import (
    DeterministicImageEmbeddingProvider,
    create_image_embedding_provider,
)
from app.providers.retrieval import (
    DeterministicEmbeddingProvider,
    ProviderError,
    ProviderIdentity,
    create_embedding_provider,
    create_reranker_provider,
)
from app.providers.storage import LocalObjectStorage
from app.retrieval.hybrid import HybridSearchService
from app.retrieval.indexing import TextEmbeddingIndexer
from app.retrieval.text_documents import DENSE_DOCUMENT_VERSION
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_PATH = WORKSPACE_ROOT / "data" / "fixtures" / "headphones.json"
ALEMBIC_CONFIG = WORKSPACE_ROOT / "services" / "api" / "alembic.ini"
EVALUATION_PATH = WORKSPACE_ROOT / "evals" / "datasets" / "stage3_lexical_queries.json"
STAGE4_EVALUATION_PATH = WORKSPACE_ROOT / "evals" / "datasets" / "stage4_text_queries.json"
STAGE5_EVALUATION_PATH = WORKSPACE_ROOT / "evals" / "datasets" / "stage5_multimodal_queries.json"


class _FailingEmbeddingProvider:
    identity = ProviderIdentity("BAAI/bge-m3", "failure-retry-v1", 1024)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        raise ProviderError("injected provider failure")


class _FailingImageEmbeddingProvider:
    identity = ProviderIdentity("google/siglip2-base-patch16-224", "failure-retry-v1", 768)

    def embed_images(self, images: Sequence[bytes]) -> list[list[float]]:
        raise ProviderError("injected image provider failure")


def _database_url(base_url: str, database_name: str) -> str:
    parsed = urlsplit(base_url)
    return urlunsplit(parsed._replace(path=f"/{database_name}"))


@pytest.mark.integration
def test_product_data_and_lexical_search_from_empty_database_through_http(tmp_path: Path) -> None:
    if os.environ.get("SHOPLENS_RUN_INTEGRATION") != "1":
        pytest.skip("set SHOPLENS_RUN_INTEGRATION=1 to test running PostgreSQL")

    base_url = str(Settings(_env_file=None).database_url)
    database_name = f"shoplens_stage3_test_{uuid4().hex}"
    temporary_url = _database_url(base_url, database_name)
    with psycopg.connect(base_url, autocommit=True) as administrator:
        administrator.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    previous_url = os.environ.get("SHOPLENS_DATABASE_URL")
    engine = None
    try:
        os.environ["SHOPLENS_DATABASE_URL"] = temporary_url
        alembic_config = Config(str(ALEMBIC_CONFIG))
        command.upgrade(alembic_config, "head")
        command.check(alembic_config)

        engine = get_engine(temporary_url)
        assert {
            "alembic_version",
            "products",
            "product_images",
            "product_documents",
            "review_evidence",
            "ingestion_jobs",
            "text_embeddings",
            "image_embeddings",
            "uploaded_image_assets",
        }.issubset(set(inspect(engine).get_table_names()))
        assert any(
            index["name"] == "ix_text_embeddings_hnsw_cosine"
            for index in inspect(engine).get_indexes("text_embeddings")
        )
        assert any(
            index["name"] == "ix_image_embeddings_hnsw_cosine"
            for index in inspect(engine).get_indexes("image_embeddings")
        )

        payload = load_fixture(FIXTURE_PATH)
        storage = LocalObjectStorage(tmp_path / "objects")
        with Session(engine) as session:
            service = IngestionService(session, storage)
            first = service.import_payload(payload, fixture_root=FIXTURE_PATH.parent)
            second = service.import_payload(payload, fixture_root=FIXTURE_PATH.parent)

            assert first.status == IngestionStatus.SUCCESS
            assert (first.succeeded, first.skipped, first.failed) == (24, 0, 0)
            assert second.status == IngestionStatus.SUCCESS
            assert (second.succeeded, second.skipped, second.failed) == (0, 24, 0)
            assert session.scalar(select(func.count(Product.id))) == 24
            assert session.scalar(select(func.count(ProductDocument.search_vector))) == 24
            assert session.scalar(select(func.count(ProductImage.id))) == 24

            invalid_payload = deepcopy(payload)
            invalid_payload["records"] = [
                {**payload["records"][0], "price_amount": "-1"},
                {**payload["records"][1], "category": "necklace"},
                {
                    **payload["records"][2],
                    "battery_life": {"value": "1", "unit": "days"},
                },
            ]
            invalid = service.import_payload(invalid_payload, fixture_root=FIXTURE_PATH.parent)
            assert invalid.status == IngestionStatus.FAILED
            assert (invalid.succeeded, invalid.skipped, invalid.failed) == (0, 0, 3)
            assert "price_amount" in invalid.errors[0].message
            assert "category" in invalid.errors[1].message
            assert "unit" in invalid.errors[2].message

            jobs = list(session.scalars(select(IngestionJob)).all())
            assert len(jobs) == 3
            assert jobs[0].finished_at is not None
            assert jobs[0].total_count == 24

            products, total = ProductRepository(session).list_products(
                ProductFilters(
                    category=ProductCategory.IN_EAR,
                    price_max=Decimal("500"),
                    currency="CNY",
                    anc=True,
                    battery_hours_min=Decimal("7"),
                    codec="AAC",
                )
            )
            assert total > 0
            assert all(product.category == ProductCategory.IN_EAR for product in products)
            assert all(product.price_amount <= 500 for product in products)
            assert all(product.anc is True for product in products)
            assert all(product.battery_hours is not None for product in products)
            assert all(product.battery_hours >= 7 for product in products if product.battery_hours)
            assert all("AAC" in product.codecs for product in products)
            detail_id = products[0].id

            exact_hits, exact_total = LexicalSearchRepository(session).search(
                "MetroTone Buds N8", ProductFilters(page_size=10)
            )
            assert exact_total == 1
            assert exact_hits[0].product.source_id == "fixture-003"

            filtered_hits, _ = LexicalSearchRepository(session).search(
                "wireless",
                ProductFilters(
                    category=ProductCategory.OVER_EAR,
                    price_max=Decimal("1000"),
                    currency="CNY",
                    anc=True,
                    page_size=10,
                ),
            )
            assert {hit.product.source_id for hit in filtered_hits} == {
                "fixture-001",
                "fixture-006",
            }
            assert all(hit.product.anc is True for hit in filtered_hits)
            assert all(hit.product.price_amount <= 1000 for hit in filtered_hits)

            dataset = EvaluationDataset.model_validate_json(
                EVALUATION_PATH.read_text(encoding="utf-8")
            )
            baseline = LexicalEvaluationRunner(LexicalSearchRepository(session)).run(dataset)
            assert baseline.query_count == 30
            assert baseline.hard_condition_violation_rate == 0
            assert baseline.empty_result_accuracy == 1

            stage4_settings = Settings(app_env="test", database_url=temporary_url, _env_file=None)
            embedding_provider = create_embedding_provider(stage4_settings)
            first_index = TextEmbeddingIndexer(
                session,
                embedding_provider,
                batch_size=stage4_settings.embedding_batch_size,
            ).run()
            second_index = TextEmbeddingIndexer(
                session,
                embedding_provider,
                batch_size=stage4_settings.embedding_batch_size,
            ).run()
            assert (first_index.indexed, first_index.skipped, first_index.failed) == (24, 0, 0)
            assert (second_index.indexed, second_index.skipped, second_index.failed) == (0, 24, 0)

            failure = TextEmbeddingIndexer(
                session, _FailingEmbeddingProvider(), batch_size=24
            ).run()
            retry_provider = DeterministicEmbeddingProvider(_FailingEmbeddingProvider.identity)
            retry = TextEmbeddingIndexer(session, retry_provider, batch_size=24).run()
            assert failure.failed == 24
            assert (retry.indexed, retry.failed) == (24, 0)

            switched_provider = DeterministicEmbeddingProvider(
                ProviderIdentity("BAAI/bge-m3", "fixture-semantic-v2", 1024)
            )
            switched = TextEmbeddingIndexer(session, switched_provider, batch_size=24).run()
            assert switched.indexed == 24
            version_rows = session.execute(
                select(TextEmbedding.model_version, func.count(TextEmbedding.id))
                .where(TextEmbedding.status == "ready")
                .group_by(TextEmbedding.model_version)
            ).all()
            version_counts: dict[str, int] = {
                model_version: count for model_version, count in version_rows
            }
            assert version_counts == {
                "failure-retry-v1": 24,
                "fixture-semantic-v1": 24,
                "fixture-semantic-v2": 24,
            }

            image_provider = create_image_embedding_provider(stage4_settings)
            first_image_index = ImageEmbeddingIndexer(
                session,
                image_provider,
                storage,
                batch_size=stage4_settings.image_embedding_batch_size,
            ).run()
            second_image_index = ImageEmbeddingIndexer(
                session,
                image_provider,
                storage,
                batch_size=stage4_settings.image_embedding_batch_size,
            ).run()
            assert (
                first_image_index.indexed,
                first_image_index.skipped,
                first_image_index.failed,
            ) == (24, 0, 0)
            assert (
                second_image_index.indexed,
                second_image_index.skipped,
                second_image_index.failed,
            ) == (0, 24, 0)

            image_failure = ImageEmbeddingIndexer(
                session,
                _FailingImageEmbeddingProvider(),
                storage,
                batch_size=24,
            ).run()
            image_retry_provider = DeterministicImageEmbeddingProvider(
                _FailingImageEmbeddingProvider.identity
            )
            image_retry = ImageEmbeddingIndexer(
                session,
                image_retry_provider,
                storage,
                batch_size=24,
            ).run()
            assert image_failure.failed == 24
            assert (image_retry.indexed, image_retry.failed) == (24, 0)

            switched_image_provider = DeterministicImageEmbeddingProvider(
                ProviderIdentity("google/siglip2-base-patch16-224", "fixture-visual-v2", 768)
            )
            switched_images = ImageEmbeddingIndexer(
                session,
                switched_image_provider,
                storage,
                batch_size=24,
            ).run()
            assert switched_images.indexed == 24
            image_version_rows = session.execute(
                select(ImageEmbedding.model_version, func.count(ImageEmbedding.id))
                .where(ImageEmbedding.status == "ready")
                .group_by(ImageEmbedding.model_version)
            ).all()
            assert {version: count for version, count in image_version_rows} == {
                "failure-retry-v1": 24,
                "fixture-visual-v1": 24,
                "fixture-visual-v2": 24,
            }

            reference_image = session.scalar(
                select(ProductImage)
                .join(Product, Product.id == ProductImage.product_id)
                .where(Product.source_id == "fixture-001")
            )
            assert reference_image is not None
            query_image_vector = image_provider.embed_images(
                [storage.resolve(reference_image.storage_key).read_bytes()]
            )[0]
            image_identity = image_provider.identity
            assert image_identity.dimension is not None
            image_hits, image_total = ImageSearchRepository(session).search(
                query_image_vector,
                ProductFilters(
                    category=ProductCategory.OVER_EAR,
                    anc=True,
                    price_max=Decimal("1000"),
                ),
                model_name=image_identity.model_name,
                model_version=image_identity.model_version,
                dimension=image_identity.dimension,
                representation_version=IMAGE_REPRESENTATION_VERSION,
                limit=10,
            )
            assert image_total == 2
            assert image_hits[0].product.source_id == "fixture-001"
            assert all(hit.product.category == ProductCategory.OVER_EAR for hit in image_hits)
            assert all(hit.product.anc is True for hit in image_hits)
            assert all(hit.product.price_amount <= 1000 for hit in image_hits)

            query_vector = embedding_provider.embed_texts(["地铁通勤降噪"])[0]
            identity = embedding_provider.identity
            assert identity.dimension is not None
            dense_hits, dense_total = DenseSearchRepository(session).search(
                query_vector,
                ProductFilters(page_size=10, anc=True, price_max=Decimal("1000")),
                model_name=identity.model_name,
                model_version=identity.model_version,
                dimension=identity.dimension,
                document_version=DENSE_DOCUMENT_VERSION,
                limit=10,
            )
            assert dense_total == 6
            assert dense_hits[0].product.source_id in {"fixture-001", "fixture-006"}
            assert all(hit.product.anc is True for hit in dense_hits)
            assert all(hit.product.price_amount <= 1000 for hit in dense_hits)

            extension = Stage4DatasetExtension.model_validate_json(
                STAGE4_EVALUATION_PATH.read_text(encoding="utf-8")
            )
            hybrid_service = HybridSearchService(
                LexicalSearchRepository(session),
                DenseSearchRepository(session),
                embedding_provider,
                create_reranker_provider(stage4_settings),
                stage4_settings,
            )
            ablation = Stage4EvaluationRunner(hybrid_service).run(
                dataset_name=extension.name,
                dataset_version=extension.version,
                corpus_product_count=extension.corpus_product_count,
                frozen_queries=dataset.queries,
                semantic_queries=extension.semantic_queries,
                parameters={"rrf_k": stage4_settings.rrf_k},
                models={"embedding": embedding_provider.identity.version_key},
            )
            assert ablation.query_count == 48
            assert all(mode.hard_condition_violation_rate == 0 for mode in ablation.modes)

            stage5_dataset = Stage5Dataset.model_validate_json(
                STAGE5_EVALUATION_PATH.read_text(encoding="utf-8")
            )
            stage5_report = Stage5EvaluationRunner(
                session,
                ImageSearchRepository(session),
                image_provider,
                storage,
                hybrid_service,
                image_candidate_k=stage4_settings.image_candidate_k,
                fusion_candidate_k=stage4_settings.fusion_candidate_k,
                rrf_k=stage4_settings.rrf_k,
                text_weight=stage4_settings.multimodal_text_weight,
                image_weight=stage4_settings.multimodal_image_weight,
            ).run(stage5_dataset)
            assert len(stage5_report.modes) == 4
            assert all(mode.hard_condition_violation_rate == 0 for mode in stage5_report.modes)

        settings = Settings(
            app_env="test",
            database_url=temporary_url,
            object_storage_path=tmp_path / "objects",
            _env_file=None,
        )
        with TestClient(create_app(settings)) as client:
            response = client.get(
                "/api/v1/products",
                params={
                    "category": "in_ear",
                    "price_max": "500",
                    "currency": "CNY",
                    "anc": "true",
                    "battery_hours_min": "7",
                    "codec": "AAC",
                },
            )
            assert response.status_code == 200
            items = response.json()["items"]
            assert items
            assert all(item["category"] == "in_ear" for item in items)
            assert all(Decimal(item["price_amount"]) <= 500 for item in items)
            assert all(item["anc"] is True for item in items)

            detail = client.get(f"/api/v1/products/{detail_id}")
            assert detail.status_code == 200
            assert detail.json()["source_url"].startswith("https://")
            assert detail.json()["price_observed_at"]

            search = client.post(
                "/api/v1/search",
                json={
                    "query": "Auralis Metro ANC 40",
                    "mode": "lexical",
                    "filters": {"category": "over_ear", "anc": True, "price_max": "1000"},
                },
            )
            assert search.status_code == 200
            assert search.json()["retrieval_mode"] == "postgresql_lexical"
            assert search.json()["items"][0]["product"]["title"] == "Auralis Metro ANC 40"

            hybrid = client.post(
                "/api/v1/search",
                json={
                    "query": "地铁通勤降噪, 戴眼镜舒适",
                    "filters": {
                        "category": "over_ear",
                        "anc": True,
                        "price_max": "1000",
                    },
                },
            )
            assert hybrid.status_code == 200
            hybrid_body = hybrid.json()
            assert hybrid_body["retrieval_mode"] == "hybrid_rerank"
            assert hybrid_body["trace"]["models"]["dense_document"] == DENSE_DOCUMENT_VERSION
            assert hybrid_body["items"]
            assert all(item["product"]["category"] == "over_ear" for item in hybrid_body["items"])
            assert all(item["product"]["anc"] is True for item in hybrid_body["items"])
            assert all(
                Decimal(item["product"]["price_amount"]) <= 1000 for item in hybrid_body["items"]
            )

            reference_bytes = (
                WORKSPACE_ROOT / "data" / "fixtures" / "images" / "fixture-001.png"
            ).read_bytes()
            invalid_upload = client.post(
                "/api/v1/assets/images",
                content=b"not a png",
                headers={"Content-Type": "image/png"},
            )
            assert invalid_upload.status_code == 422
            upload = client.post(
                "/api/v1/assets/images",
                content=reference_bytes,
                headers={"Content-Type": "image/png"},
            )
            assert upload.status_code == 201
            asset = upload.json()
            assert asset["media_type"] == "image/webp"
            assert asset["width"] == 320

            image_search = client.post(
                "/api/v1/multimodal-search",
                json={
                    "asset_id": asset["asset_id"],
                    "filters": {
                        "category": "over_ear",
                        "anc": True,
                        "price_max": "1000",
                    },
                },
            )
            assert image_search.status_code == 200
            image_body = image_search.json()
            assert image_body["retrieval_mode"] == "pgvector_image"
            assert image_body["items"][0]["product"]["source_name"] == (
                "shoplens_deterministic_fixture"
            )
            assert all(item["product"]["category"] == "over_ear" for item in image_body["items"])
            assert all(item["product"]["anc"] is True for item in image_body["items"])
            assert all(
                Decimal(item["product"]["price_amount"]) <= 1000 for item in image_body["items"]
            )

            multimodal = client.post(
                "/api/v1/multimodal-search",
                json={
                    "asset_id": asset["asset_id"],
                    "query": "通勤降噪 戴眼镜舒适",
                    "filters": {
                        "category": "over_ear",
                        "anc": True,
                        "price_max": "1000",
                    },
                },
            )
            assert multimodal.status_code == 200
            multimodal_body = multimodal.json()
            assert multimodal_body["retrieval_mode"] == "multimodal_rrf"
            assert multimodal_body["trace"]["channels"]["image"]
            assert all(
                item["product"]["category"] == "over_ear" for item in multimodal_body["items"]
            )

            assistant = client.post(
                "/api/v1/assistant/query",
                json={"message": "预算 1000 元以内, 头戴式主动降噪, 适合地铁通勤"},
            )
            assert assistant.status_code == 200
            assistant_body = assistant.json()
            assert assistant_body["status"] == "completed"
            assert assistant_body["recommendations"]
            assert assistant_body["trace"]["citation_validation"]["valid"] is True
            assert len(assistant_body["trace"]["tool_steps"]) <= 4
            assert all(
                item["product"]["category"] == "over_ear"
                for item in assistant_body["recommendations"]
            )
            assert all(item["product"]["anc"] is True for item in assistant_body["recommendations"])
            assert all(
                Decimal(item["product"]["price_amount"]) <= 1000
                for item in assistant_body["recommendations"]
            )

            session_context = client.get(f"/api/v1/sessions/{assistant_body['session_id']}")
            trace_detail = client.get(f"/api/v1/traces/{assistant_body['trace_id']}")
            assert session_context.status_code == 200
            assert session_context.json()["filters"]["price_max"] == "1000"
            assert trace_detail.status_code == 200

            follow_up = client.post(
                "/api/v1/assistant/query",
                json={
                    "message": "清除预算, 继续找头戴式降噪耳机",
                    "session_id": assistant_body["session_id"],
                },
            )
            assert follow_up.status_code == 200
            assert follow_up.json()["applied_filters"]["price_max"] is None
            assert follow_up.json()["applied_filters"]["anc"] is True

            comparison_ids = [
                item["product"]["id"] for item in assistant_body["recommendations"][:2]
            ]
            assert len(comparison_ids) == 2
            comparison = client.post(
                "/api/v1/products/compare", json={"product_ids": comparison_ids}
            )
            assert comparison.status_code == 200
            assert len(comparison.json()["comparison"]["product_ids"]) == 2
    finally:
        if engine is not None:
            engine.dispose()
        get_engine.cache_clear()
        if previous_url is None:
            os.environ.pop("SHOPLENS_DATABASE_URL", None)
        else:
            os.environ["SHOPLENS_DATABASE_URL"] = previous_url
        with psycopg.connect(base_url, autocommit=True) as administrator:
            administrator.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (database_name,),
            )
            administrator.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(database_name)))
