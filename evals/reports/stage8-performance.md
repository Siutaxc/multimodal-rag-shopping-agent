# Stage 8 synthetic scale performance

- Generated: `2026-07-22T08:02:52.744984+00:00`
- Data: deterministic synthetic copies of the 24 CC0 fixtures; not real products.
- Environment: `{'platform': 'Windows-11-10.0.26200-SP0', 'python': '3.13.7', 'cpu_count': 12, 'postgres': 'PostgreSQL 16.14 (Debian 16.14-1.pgdg12+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit', 'pgvector': '0.8.5'}`
- Each latency is measured after 3 warmups; P50/P95 use client wall-clock samples.

| Products | Phase | Operation | P50 ms | P95 ms | Samples |
|---:|---|---|---:|---:|---:|
| 5000 | before_indexes | structured_filter | 1.575 | 2.219 | 20 |
| 5000 | before_indexes | lexical_search | 3.487 | 5.072 | 20 |
| 5000 | before_indexes | dense_ann | 34.756 | 40.278 | 20 |
| 5000 | after_indexes | structured_filter | 0.461 | 0.631 | 20 |
| 5000 | after_indexes | lexical_search | 1.010 | 1.353 | 20 |
| 5000 | after_indexes | dense_ann | 0.572 | 0.667 | 20 |
| 50000 | before_indexes | structured_filter | 20.256 | 23.389 | 20 |
| 50000 | before_indexes | lexical_search | 31.013 | 39.634 | 20 |
| 50000 | before_indexes | dense_ann | 227.514 | 239.207 | 20 |
| 50000 | after_indexes | structured_filter | 0.378 | 0.462 | 20 |
| 50000 | after_indexes | lexical_search | 8.753 | 10.681 | 20 |
| 50000 | after_indexes | dense_ann | 0.648 | 1.113 | 20 |

## Build cost and bottleneck evidence

- 5000 products: population 2.185s; indexes 1.192s. Full EXPLAIN ANALYZE/BUFFERS plans are retained in the JSON report.
- 50000 products: population 18.151s; indexes 17.748s. Full EXPLAIN ANALYZE/BUFFERS plans are retained in the JSON report.

## Limitations

- Repeated fixture vectors create duplicate-neighbor clusters and do not model real catalog embedding diversity.
- This isolates PostgreSQL filter/FTS/ANN behavior; HTTP, Redis, and model-provider latency are measured separately by API metrics and fault tests.
- UNLOGGED benchmark rows are removed by default after measurement.
