"""Benchmark 5k/50k explicitly synthetic copies without modifying canonical products."""

import argparse
import json
import math
import os
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Any

import psycopg
from psycopg import Connection

from app.core.settings import Settings

_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
_TABLE = "shoplens_stage8_benchmark_products"


@dataclass(frozen=True)
class OperationResult:
    operation: str
    p50_ms: float
    p95_ms: float
    samples: int
    plan: dict[str, Any]


@dataclass(frozen=True)
class ScaleResult:
    product_count: int
    population_seconds: float
    index_build_seconds: float
    before_indexes: list[OperationResult]
    after_indexes: list[OperationResult]


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * percentile) - 1)]


def _measure(
    connection: Connection[Any], operation: str, statement: str, samples: int
) -> OperationResult:
    with connection.cursor() as cursor:
        for _ in range(3):
            cursor.execute(statement)
            cursor.fetchall()
        durations: list[float] = []
        for _ in range(samples):
            started = perf_counter()
            cursor.execute(statement)
            cursor.fetchall()
            durations.append((perf_counter() - started) * 1000)
        cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {statement}")
        row = cursor.fetchone()
    raw_plan = row[0] if row else []
    plan = raw_plan[0] if isinstance(raw_plan, list) and raw_plan else {}
    return OperationResult(
        operation=operation,
        p50_ms=round(median(durations), 3),
        p95_ms=round(_percentile(durations, 0.95), 3),
        samples=samples,
        plan=plan,
    )


def _drop_table(connection: Connection[Any]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {_TABLE}")
    connection.commit()


def _populate(connection: Connection[Any], count: int, settings: Settings) -> float:
    _drop_table(connection)
    started = perf_counter()
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            CREATE UNLOGGED TABLE {_TABLE} (
                synthetic_id bigint PRIMARY KEY,
                base_source_id text NOT NULL,
                title text NOT NULL,
                brand text NOT NULL,
                category text NOT NULL,
                price_amount numeric(12,2) NOT NULL,
                currency text NOT NULL,
                wireless boolean,
                anc boolean,
                battery_hours numeric(7,2),
                search_text text NOT NULL,
                search_vector tsvector GENERATED ALWAYS AS
                    (to_tsvector('simple'::regconfig, search_text)) STORED,
                embedding vector(1024) NOT NULL
            )
            """
        )
        cursor.execute(
            f"""
            INSERT INTO {_TABLE} (
                synthetic_id, base_source_id, title, brand, category, price_amount,
                currency, wireless, anc, battery_hours, search_text, embedding
            )
            SELECT
                generated.synthetic_id,
                base.source_id,
                base.title || ' synthetic-copy-' || generated.synthetic_id,
                base.brand,
                base.category,
                base.price_amount + (generated.synthetic_id %% 17),
                base.currency,
                base.wireless,
                base.anc,
                base.battery_hours,
                base.search_text || ' synthetic copy ' || generated.synthetic_id,
                base.embedding
            FROM generate_series(1, %s) AS generated(synthetic_id)
            JOIN LATERAL (
                SELECT
                    p.source_id, p.title, p.brand, p.category, p.price_amount,
                    p.currency, p.wireless, p.anc, p.battery_hours,
                    pd.search_text, te.embedding
                FROM products p
                JOIN product_documents pd ON pd.product_id = p.id
                JOIN text_embeddings te ON te.document_id = pd.id
                WHERE pd.document_type = 'MAIN'
                  AND te.model_name = %s
                  AND te.model_version = %s
                  AND te.dimension = 1024
                  AND te.document_version = 'stage4-dense-v1'
                  AND te.status = 'ready'
                  AND te.embedding IS NOT NULL
                ORDER BY p.source_id
                OFFSET ((generated.synthetic_id - 1) %% 24)
                LIMIT 1
            ) AS base ON true
            """,
            (count, settings.embedding_model_name, settings.embedding_model_version),
        )
        cursor.execute(f"ANALYZE {_TABLE}")
    connection.commit()
    return round(perf_counter() - started, 3)


def _build_indexes(connection: Connection[Any]) -> float:
    started = perf_counter()
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE INDEX stage8_bench_hard_filters ON {_TABLE} "
            "(category, currency, anc, wireless, price_amount, synthetic_id)"
        )
        cursor.execute(
            f"CREATE INDEX stage8_bench_lexical_gin ON {_TABLE} USING gin (search_vector)"
        )
        cursor.execute(
            f"CREATE INDEX stage8_bench_embedding_hnsw ON {_TABLE} USING hnsw "
            "(embedding vector_cosine_ops) WITH (m=16, ef_construction=64)"
        )
        cursor.execute(f"ANALYZE {_TABLE}")
    connection.commit()
    return round(perf_counter() - started, 3)


def _operations() -> tuple[tuple[str, str], ...]:
    return (
        (
            "structured_filter",
            f"SELECT synthetic_id FROM {_TABLE} WHERE category = 'OVER_EAR' "
            "AND currency = 'CNY' AND anc IS TRUE AND wireless IS TRUE "
            "AND price_amount <= 1000 ORDER BY price_amount, synthetic_id LIMIT 30",
        ),
        (
            "lexical_search",
            f"SELECT synthetic_id FROM {_TABLE} WHERE search_vector @@ "
            "websearch_to_tsquery('simple', 'Auralis Metro ANC') "
            "ORDER BY ts_rank_cd(search_vector, "
            "websearch_to_tsquery('simple', 'Auralis Metro ANC'), 32) DESC, synthetic_id LIMIT 30",
        ),
        (
            "dense_ann",
            f"SELECT synthetic_id FROM {_TABLE} ORDER BY embedding <=> "
            f"(SELECT embedding FROM {_TABLE} WHERE synthetic_id = 1) LIMIT 30",
        ),
    )


def _run_scale(
    connection: Connection[Any], count: int, samples: int, settings: Settings
) -> ScaleResult:
    population_seconds = _populate(connection, count, settings)
    before = [
        _measure(connection, operation, statement, samples)
        for operation, statement in _operations()
    ]
    index_seconds = _build_indexes(connection)
    after = [
        _measure(connection, operation, statement, samples)
        for operation, statement in _operations()
    ]
    return ScaleResult(count, population_seconds, index_seconds, before, after)


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stage 8 synthetic scale performance",
        "",
        f"- Generated: `{report['generated_at']}`",
        "- Data: deterministic synthetic copies of the 24 CC0 fixtures; not real products.",
        f"- Environment: `{report['environment']}`",
        "- Each latency is measured after 3 warmups; P50/P95 use client wall-clock samples.",
        "",
        "| Products | Phase | Operation | P50 ms | P95 ms | Samples |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for scale in report["scales"]:
        for phase in ("before_indexes", "after_indexes"):
            for item in scale[phase]:
                lines.append(
                    f"| {scale['product_count']} | {phase} | {item['operation']} | "
                    f"{item['p50_ms']:.3f} | {item['p95_ms']:.3f} | {item['samples']} |"
                )
    lines.extend(
        [
            "",
            "## Build cost and bottleneck evidence",
            "",
            *[
                f"- {scale['product_count']} products: population "
                f"{scale['population_seconds']:.3f}s; indexes "
                f"{scale['index_build_seconds']:.3f}s. Full EXPLAIN ANALYZE/BUFFERS plans "
                "are retained in the JSON report."
                for scale in report["scales"]
            ],
            "",
            "## Limitations",
            "",
            "- Repeated fixture vectors create duplicate-neighbor clusters and do not model "
            "real catalog embedding diversity.",
            "- This isolates PostgreSQL filter/FTS/ANN behavior; HTTP, Redis, and model-provider "
            "latency are measured separately by API metrics and fault tests.",
            "- UNLOGGED benchmark rows are removed by default after measurement.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run synthetic 5k/50k PostgreSQL benchmarks")
    parser.add_argument("--scales", nargs="+", type=int, default=[5_000, 50_000])
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--keep-table", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=_WORKSPACE_ROOT / "evals/reports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if any(scale not in {5_000, 50_000} for scale in args.scales):
        raise ValueError("stage-eight scale must be 5000 or 50000")
    if args.samples < 5:
        raise ValueError("at least five measured samples are required")
    settings = Settings()
    scales: list[ScaleResult] = []
    with psycopg.connect(str(settings.database_url)) as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                postgres_row = cursor.fetchone()
                if postgres_row is None:
                    raise RuntimeError("PostgreSQL version query returned no row")
                postgres_version = str(postgres_row[0])
                cursor.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
                vector_row = cursor.fetchone()
                if vector_row is None:
                    raise RuntimeError("pgvector extension is not installed")
                vector_version = str(vector_row[0])
            for scale in args.scales:
                scales.append(_run_scale(connection, scale, args.samples, settings))
        finally:
            if not args.keep_table:
                _drop_table(connection)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "synthetic_data": True,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "cpu_count": os.cpu_count(),
            "postgres": postgres_version,
            "pgvector": vector_version,
        },
        "scales": [asdict(scale) for scale in scales],
    }
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stage8-performance.json"
    markdown_path = output_dir / "stage8-performance.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
    markdown_path.write_text(_markdown(report), "utf-8")
    print(json.dumps({"json": str(json_path), "markdown": str(markdown_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
