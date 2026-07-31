"""Generate the deterministic, reviewable stage-eight query extension."""

import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]


def main() -> int:
    fixture = json.loads(
        (WORKSPACE / "data/fixtures/headphones.json").read_text(encoding="utf-8")
    )
    records = fixture["records"]
    queries: list[dict[str, object]] = []
    query_id = 1
    for record in records:
        source_id = record["source_id"]
        title = record["title"]
        brand = record["brand"]
        price = record["price_amount"]
        for query in (title, f"{brand} {title}", f"{title} 价格 {price} CNY"):
            queries.append(
                {
                    "id": f"s8-{query_id:03d}",
                    "query": query,
                    "relevance": {source_id: 3},
                    "filters": {},
                    "cohort": "product_identity",
                }
            )
            query_id += 1

    for record in records[:18]:
        queries.append(
            {
                "id": f"s8-{query_id:03d}",
                "query": record["title"],
                "relevance": {},
                "filters": {"currency": "CNY", "price_max": "0.00"},
                "cohort": "adversarial_empty",
            }
        )
        query_id += 1

    scenarios = (
        ("通勤地铁主动降噪，预算七百元", ["fixture-003", "fixture-006"]),
        ("开放式跑步耳机，防水至少 IP55", ["fixture-009"]),
        ("游泳训练骨传导 IP68", ["fixture-011"]),
        ("办公室开会要杆式麦克风", ["fixture-007", "fixture-012", "fixture-013"]),
        ("百元以内有线入耳通话", ["fixture-016"]),
        ("长续航折叠旅行降噪头戴", ["fixture-006"]),
        ("戴眼镜也舒适的通勤头戴耳机", ["fixture-001"]),
        ("不要堵耳的轻量耳夹", ["fixture-019", "fixture-020"]),
        ("高阻抗有线头戴室内听音", ["fixture-024"]),
        ("五百元内小巧入耳主动降噪", ["fixture-003"]),
        ("抗风噪户外通话无线耳机", ["fixture-006", "fixture-009"]),
        ("半入耳无线通话，三百元内", ["fixture-004", "fixture-023"]),
    )
    for query, source_ids in scenarios:
        queries.append(
            {
                "id": f"s8-{query_id:03d}",
                "query": query,
                "relevance": {source_id: 3 for source_id in source_ids},
                "filters": {},
                "cohort": "scenario",
            }
        )
        query_id += 1

    payload = {
        "name": "shoplens-stage8-expanded-text-ablation",
        "version": "2026-07-22.1",
        "frozen_lexical_dataset": "evals/datasets/stage3_lexical_queries.json",
        "frozen_semantic_dataset": "evals/datasets/stage4_text_queries.json",
        "fixture_source_version": fixture["source_version"],
        "corpus_product_count": len(records),
        "license": "CC0-1.0; generated entirely from the synthetic ShopLens fixture",
        "queries": queries,
    }
    if len(queries) != 102:
        raise RuntimeError(f"expected 102 new queries, got {len(queries)}")
    output = WORKSPACE / "evals/datasets/stage8_text_queries.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
