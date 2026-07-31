"""Deterministic checks for the stage-three dataset and metric definitions."""

import json
from pathlib import Path

import pytest
from app.evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank
from app.evaluation.schemas import EvaluationDataset
from app.evaluation.stage4_schemas import Stage4DatasetExtension

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def test_stage3_dataset_has_30_queries_and_only_fixture_source_ids() -> None:
    dataset_path = _WORKSPACE_ROOT / "evals/datasets/stage3_lexical_queries.json"
    fixture_path = _WORKSPACE_ROOT / "data/fixtures/headphones.json"
    dataset = EvaluationDataset.model_validate_json(dataset_path.read_text(encoding="utf-8"))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture_ids = {record["source_id"] for record in fixture["records"]}

    assert len(dataset.queries) == 30
    assert dataset.fixture_source_version == fixture["source_version"]
    assert all(set(query.relevance) <= fixture_ids for query in dataset.queries)


def test_retrieval_metrics_have_explicit_cutoff_semantics() -> None:
    retrieved = ["b", "x", "a"]
    relevance = {"a": 3, "b": 1}

    assert recall_at_k(retrieved, set(relevance), 2) == pytest.approx(0.5)
    assert recall_at_k(retrieved, set(relevance), 3) == pytest.approx(1.0)
    assert precision_at_k(retrieved, set(relevance), 5) == pytest.approx(0.4)
    assert reciprocal_rank(retrieved, set(relevance)) == pytest.approx(1.0)
    assert 0 < ndcg_at_k(retrieved, relevance, 3) < 1


def test_metric_edge_cases_are_stable() -> None:
    assert recall_at_k([], {"a"}, 10) == 0
    assert reciprocal_rank(["x"], {"a"}) == 0
    assert ndcg_at_k([], {"a": 3}, 10) == 0
    with pytest.raises(ValueError, match="k must be positive"):
        precision_at_k([], {"a"}, 0)


def test_stage4_extension_keeps_stage3_frozen_and_adds_semantic_queries() -> None:
    extension_path = _WORKSPACE_ROOT / "evals/datasets/stage4_text_queries.json"
    extension = Stage4DatasetExtension.model_validate_json(
        extension_path.read_text(encoding="utf-8")
    )

    assert extension.base_dataset == "evals/datasets/stage3_lexical_queries.json"
    assert len(extension.semantic_queries) >= 10
    assert any("戴眼镜" in query.query for query in extension.semantic_queries)
    assert any(not query.relevance for query in extension.semantic_queries)
