# Stage 8 expanded text retrieval ablation

- Dataset: `shoplens-stage8-expanded-text-ablation` / `2026-07-22.1`
- Corpus: 24 synthetic CC0 fixtures
- Queries: 150 (30 frozen lexical + 120 semantic)
- Generated: `2026-07-22T08:01:07.812476+00:00`
- Models: `{'embedding': 'BAAI/bge-m3@fixture-semantic-v1:1024', 'reranker': 'BAAI/bge-reranker-v2-m3@fixture-semantic-v1'}`
- Parameters: `{'lexical_candidate_k': 50, 'dense_candidate_k': 50, 'fusion_candidate_k': 30, 'rerank_top_k': 30, 'rrf_k': 60}`

| Mode | R@5 | R@10 | P@5 | nDCG@10 | MRR | Hard violations | Empty accuracy | P50 ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.5888 | 0.5923 | 0.1754 | 0.5923 | 0.5923 | 0.0000 | 1.0000 | 3.176 | 7.512 |
| dense | 0.9498 | 0.9772 | 0.2754 | 0.9072 | 0.8914 | 0.0000 | 1.0000 | 6.692 | 10.689 |
| rrf | 0.9555 | 0.9821 | 0.2815 | 0.9464 | 0.9375 | 0.0000 | 1.0000 | 10.366 | 17.502 |
| rerank | 0.9498 | 0.9772 | 0.2754 | 0.9072 | 0.8914 | 0.0000 | 1.0000 | 26.674 | 38.218 |

## Failure analysis

- **lexical**: sem-01, sem-02, sem-03, sem-04, sem-05, sem-06, sem-07, sem-08, sem-09, sem-10, sem-11, sem-12, sem-13, sem-14, sem-15, sem-16, sem-18, s8-003, s8-006, s8-009, s8-012, s8-015, s8-018, s8-021, s8-024, s8-027, s8-030, s8-033, s8-036, s8-039, s8-042, s8-045, s8-048, s8-051, s8-054, s8-057, s8-060, s8-063, s8-066, s8-069, s8-072, s8-091, s8-092, s8-093, s8-094, s8-095, s8-096, s8-097, s8-098, s8-099, s8-100, s8-101, s8-102
- **dense**: lex-01, lex-08, lex-10, lex-16, lex-21, lex-22, sem-01, sem-03, sem-04, sem-06, sem-08, sem-10, sem-18, s8-001, s8-002, s8-003, s8-008, s8-014, s8-043, s8-044, s8-045, s8-052, s8-053, s8-054, s8-066, s8-091, s8-092, s8-098, s8-100, s8-101, s8-102
- **rrf**: sem-01, sem-03, sem-04, sem-06, sem-08, sem-10, sem-18, s8-003, s8-045, s8-054, s8-066, s8-091, s8-092, s8-098, s8-100, s8-101, s8-102
- **rerank**: lex-01, lex-08, lex-10, lex-16, lex-21, lex-22, sem-01, sem-03, sem-04, sem-06, sem-08, sem-10, sem-18, s8-001, s8-002, s8-003, s8-008, s8-014, s8-043, s8-044, s8-045, s8-052, s8-053, s8-054, s8-066, s8-091, s8-092, s8-098, s8-100, s8-101, s8-102

## Limitations

- The 150 queries target only 24 synthetic CC0 fixture products.
- The expanded exact, adversarial, and scenario cohorts are engineering regression data, not an independent production relevance judgment set.
- Deterministic fixture providers prove reproducibility and failure handling, not real BGE-M3 or reranker quality.
- Every failed query remains in the JSON and Markdown reports.

## Complete query trace

### lexical

| ID | Query | Expected | Retrieved | R@10 | nDCG@10 | Violations | Degraded |
|---|---|---|---|---:|---:|---:|---|
| lex-01 | Auralis Metro ANC 40 | fixture-001 | fixture-001 | 1.000 | 1.000 | 0 | — |
| lex-02 | Auralis Studio ANC 55 | fixture-002 | fixture-002 | 1.000 | 1.000 | 0 | — |
| lex-03 | MetroTone Buds N8 | fixture-003 | fixture-003 | 1.000 | 1.000 | 0 | — |
| lex-04 | QuietArc Q3 Travel | fixture-006 | fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-05 | OpenPath Loop 14 | fixture-009 | fixture-009 | 1.000 | 1.000 | 0 | — |
| lex-06 | BoneWave Swim B2 | fixture-011 | fixture-011 | 1.000 | 1.000 | 0 | — |
| lex-07 | ClearCall Work C40 ANC | fixture-013 | fixture-013 | 1.000 | 1.000 | 0 | — |
| lex-08 | Auralis Pocket P4 ANC | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 | — |
| lex-09 | MetroTone Cable M1 | fixture-016 | fixture-016 | 1.000 | 1.000 | 0 | — |
| lex-10 | QuietArc Q7 Reference | fixture-018 | fixture-018 | 1.000 | 1.000 | 0 | — |
| lex-11 | OpenPath Clip O5 | fixture-020 | fixture-020 | 1.000 | 1.000 | 0 | — |
| lex-12 | ClearCall Bud C8 | fixture-022 | fixture-022 | 1.000 | 1.000 | 0 | — |
| lex-13 | Auralis | fixture-001, fixture-002, fixture-014, fixture-015, fixture-024 | fixture-001, fixture-014, fixture-015, fixture-002, fixture-024 | 1.000 | 1.000 | 0 | — |
| lex-14 | QuietArc | fixture-005, fixture-006, fixture-007, fixture-018 | fixture-005, fixture-006, fixture-007, fixture-018 | 1.000 | 1.000 | 0 | — |
| lex-15 | BoneWave | fixture-010, fixture-011, fixture-021 | fixture-021, fixture-010, fixture-011 | 1.000 | 1.000 | 0 | — |
| lex-16 | 主动降噪 | fixture-001, fixture-002, fixture-003, fixture-006, fixture-013, fixture-015, fixture-022 | fixture-001, fixture-015, fixture-002, fixture-022, fixture-013, fixture-003, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-17 | 骨传导 | fixture-010, fixture-011, fixture-021 | fixture-021, fixture-010, fixture-011 | 1.000 | 1.000 | 0 | — |
| lex-18 | 开放式 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-019, fixture-020, fixture-008, fixture-009 | 1.000 | 1.000 | 0 | — |
| lex-19 | 半入耳式 | fixture-004, fixture-017, fixture-023 | fixture-023, fixture-004, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-20 | 有线 | fixture-016, fixture-017, fixture-018, fixture-024 | fixture-024, fixture-016, fixture-017, fixture-018 | 1.000 | 1.000 | 0 | — |
| lex-21 | 通话 入耳式 | fixture-003, fixture-014, fixture-015, fixture-016, fixture-022 | fixture-016, fixture-014, fixture-022, fixture-003, fixture-015 | 1.000 | 1.000 | 0 | — |
| lex-22 | 通勤 | fixture-001, fixture-021 | fixture-001, fixture-021 | 1.000 | 1.000 | 0 | — |
| lex-23 | 办公 | fixture-007, fixture-012, fixture-013 | fixture-012, fixture-013, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-24 | 户外 运动 | fixture-010 | fixture-010 | 1.000 | 1.000 | 0 | — |
| lex-25 | headphones | fixture-004, fixture-014, fixture-016, fixture-017, fixture-019, fixture-023 | fixture-014, fixture-023, fixture-004, fixture-016, fixture-017, fixture-019 | 1.000 | 1.000 | 0 | — |
| lex-26 | wireless | fixture-001, fixture-006 | fixture-001, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-27 | wireless | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 | — |
| lex-28 | microphone | fixture-012, fixture-013, fixture-022 | fixture-022, fixture-012, fixture-013 | 1.000 | 1.000 | 0 | — |
| lex-29 | headphones | fixture-014 | fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-30 | headphones | ∅ | ∅ | n/a | n/a | 0 | — |
| sem-01 | 地铁里想安静一点的通勤耳机 | fixture-001, fixture-002, fixture-006 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-02 | 戴眼镜长时间听歌，不要太夹头 | fixture-001 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-03 | 开会时人声清楚的办公耳机 | fixture-007, fixture-012, fixture-013 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-04 | 跑步时还能听到周围环境 | fixture-008, fixture-009, fixture-010 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-05 | 游泳训练用，防水要可靠 | fixture-011 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-06 | 一周少充电的长续航头戴耳机 | fixture-001, fixture-002, fixture-006 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-07 | 不想塞耳朵，还要能听见环境音 | fixture-008, fixture-009, fixture-019, fixture-020 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-08 | 五百元内地铁通勤降噪入耳耳机 | fixture-003 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-09 | 视频会议麦克风清晰，不要入耳式 | fixture-007, fixture-012, fixture-013 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-10 | 户外雨天运动，防水耐用 | fixture-009, fixture-010, fixture-011 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-11 | 便携小巧，适合每天随身带 | fixture-003, fixture-014 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-12 | 喜欢人声靠前、低频适中的声音 | fixture-003 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-13 | 旅行收纳方便、可以折叠的降噪耳机 | fixture-006 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-14 | 高阻抗，适合室内安静听音 | fixture-018, fixture-024 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-15 | 耳朵敏感，不堵耳而且轻量 | fixture-008, fixture-009, fixture-019, fixture-020 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-16 | 便宜的有线耳塞，用来打电话 | fixture-016 | ∅ | 0.000 | 0.000 | 0 | — |
| sem-17 | 一百元内无线头戴主动降噪 | ∅ | ∅ | n/a | n/a | 0 | — |
| sem-18 | 户外通话时减少风噪 | fixture-006, fixture-009 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-001 | Auralis Metro ANC 40 | fixture-001 | fixture-001 | 1.000 | 1.000 | 0 | — |
| s8-002 | Auralis Auralis Metro ANC 40 | fixture-001 | fixture-001 | 1.000 | 1.000 | 0 | — |
| s8-003 | Auralis Metro ANC 40 价格 899.00 CNY | fixture-001 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-004 | Auralis Studio ANC 55 | fixture-002 | fixture-002 | 1.000 | 1.000 | 0 | — |
| s8-005 | Auralis Auralis Studio ANC 55 | fixture-002 | fixture-002 | 1.000 | 1.000 | 0 | — |
| s8-006 | Auralis Studio ANC 55 价格 1299.00 CNY | fixture-002 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-007 | MetroTone Buds N8 | fixture-003 | fixture-003 | 1.000 | 1.000 | 0 | — |
| s8-008 | MetroTone MetroTone Buds N8 | fixture-003 | fixture-003 | 1.000 | 1.000 | 0 | — |
| s8-009 | MetroTone Buds N8 价格 499.00 CNY | fixture-003 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-010 | MetroTone Air S2 | fixture-004 | fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-011 | MetroTone MetroTone Air S2 | fixture-004 | fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-012 | MetroTone Air S2 价格 199.00 CNY | fixture-004 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-013 | QuietArc Q1 Lite | fixture-005 | fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-014 | QuietArc QuietArc Q1 Lite | fixture-005 | fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-015 | QuietArc Q1 Lite 价格 399.00 CNY | fixture-005 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-016 | QuietArc Q3 Travel | fixture-006 | fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-017 | QuietArc QuietArc Q3 Travel | fixture-006 | fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-018 | QuietArc Q3 Travel 价格 699.00 CNY | fixture-006 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-019 | QuietArc Q5 Office | fixture-007 | fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-020 | QuietArc QuietArc Q5 Office | fixture-007 | fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-021 | QuietArc Q5 Office 价格 559.00 CNY | fixture-007 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-022 | OpenPath Loop 10 | fixture-008 | fixture-008 | 1.000 | 1.000 | 0 | — |
| s8-023 | OpenPath OpenPath Loop 10 | fixture-008 | fixture-008 | 1.000 | 1.000 | 0 | — |
| s8-024 | OpenPath Loop 10 价格 459.00 CNY | fixture-008 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-025 | OpenPath Loop 14 | fixture-009 | fixture-009 | 1.000 | 1.000 | 0 | — |
| s8-026 | OpenPath OpenPath Loop 14 | fixture-009 | fixture-009 | 1.000 | 1.000 | 0 | — |
| s8-027 | OpenPath Loop 14 价格 659.00 CNY | fixture-009 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-028 | BoneWave Run B1 | fixture-010 | fixture-010 | 1.000 | 1.000 | 0 | — |
| s8-029 | BoneWave BoneWave Run B1 | fixture-010 | fixture-010 | 1.000 | 1.000 | 0 | — |
| s8-030 | BoneWave Run B1 价格 379.00 CNY | fixture-010 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-031 | BoneWave Swim B2 | fixture-011 | fixture-011 | 1.000 | 1.000 | 0 | — |
| s8-032 | BoneWave BoneWave Swim B2 | fixture-011 | fixture-011 | 1.000 | 1.000 | 0 | — |
| s8-033 | BoneWave Swim B2 价格 799.00 CNY | fixture-011 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-034 | ClearCall Work C20 | fixture-012 | fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-035 | ClearCall ClearCall Work C20 | fixture-012 | fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-036 | ClearCall Work C20 价格 329.00 CNY | fixture-012 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-037 | ClearCall Work C40 ANC | fixture-013 | fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-038 | ClearCall ClearCall Work C40 ANC | fixture-013 | fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-039 | ClearCall Work C40 ANC 价格 749.00 CNY | fixture-013 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-040 | Auralis Pocket P2 | fixture-014 | fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-041 | Auralis Auralis Pocket P2 | fixture-014 | fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-042 | Auralis Pocket P2 价格 259.00 CNY | fixture-014 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-043 | Auralis Pocket P4 ANC | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 | — |
| s8-044 | Auralis Auralis Pocket P4 ANC | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 | — |
| s8-045 | Auralis Pocket P4 ANC 价格 599.00 CNY | fixture-015 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-046 | MetroTone Cable M1 | fixture-016 | fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-047 | MetroTone MetroTone Cable M1 | fixture-016 | fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-048 | MetroTone Cable M1 价格 99.00 CNY | fixture-016 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-049 | MetroTone Cable M3 | fixture-017 | fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-050 | MetroTone MetroTone Cable M3 | fixture-017 | fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-051 | MetroTone Cable M3 价格 129.00 CNY | fixture-017 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-052 | QuietArc Q7 Reference | fixture-018 | fixture-018 | 1.000 | 1.000 | 0 | — |
| s8-053 | QuietArc QuietArc Q7 Reference | fixture-018 | fixture-018 | 1.000 | 1.000 | 0 | — |
| s8-054 | QuietArc Q7 Reference 价格 999.00 CNY | fixture-018 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-055 | OpenPath Clip O2 | fixture-019 | fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-056 | OpenPath OpenPath Clip O2 | fixture-019 | fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-057 | OpenPath Clip O2 价格 299.00 CNY | fixture-019 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-058 | OpenPath Clip O5 | fixture-020 | fixture-020 | 1.000 | 1.000 | 0 | — |
| s8-059 | OpenPath OpenPath Clip O5 | fixture-020 | fixture-020 | 1.000 | 1.000 | 0 | — |
| s8-060 | OpenPath Clip O5 价格 549.00 CNY | fixture-020 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-061 | BoneWave City B3 | fixture-021 | fixture-021 | 1.000 | 1.000 | 0 | — |
| s8-062 | BoneWave BoneWave City B3 | fixture-021 | fixture-021 | 1.000 | 1.000 | 0 | — |
| s8-063 | BoneWave City B3 价格 469.00 CNY | fixture-021 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-064 | ClearCall Bud C8 | fixture-022 | fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-065 | ClearCall ClearCall Bud C8 | fixture-022 | fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-066 | ClearCall Bud C8 价格 429.00 CNY | fixture-022 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-067 | ClearCall Air C5 | fixture-023 | fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-068 | ClearCall ClearCall Air C5 | fixture-023 | fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-069 | ClearCall Air C5 价格 279.00 CNY | fixture-023 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-070 | Auralis Studio Wired 80 | fixture-024 | fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-071 | Auralis Auralis Studio Wired 80 | fixture-024 | fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-072 | Auralis Studio Wired 80 价格 1599.00 CNY | fixture-024 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-073 | Auralis Metro ANC 40 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-074 | Auralis Studio ANC 55 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-075 | MetroTone Buds N8 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-076 | MetroTone Air S2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-077 | QuietArc Q1 Lite | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-078 | QuietArc Q3 Travel | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-079 | QuietArc Q5 Office | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-080 | OpenPath Loop 10 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-081 | OpenPath Loop 14 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-082 | BoneWave Run B1 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-083 | BoneWave Swim B2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-084 | ClearCall Work C20 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-085 | ClearCall Work C40 ANC | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-086 | Auralis Pocket P2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-087 | Auralis Pocket P4 ANC | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-088 | MetroTone Cable M1 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-089 | MetroTone Cable M3 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-090 | QuietArc Q7 Reference | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-091 | 通勤地铁主动降噪，预算七百元 | fixture-003, fixture-006 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-092 | 开放式跑步耳机，防水至少 IP55 | fixture-009 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-093 | 游泳训练骨传导 IP68 | fixture-011 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-094 | 办公室开会要杆式麦克风 | fixture-007, fixture-012, fixture-013 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-095 | 百元以内有线入耳通话 | fixture-016 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-096 | 长续航折叠旅行降噪头戴 | fixture-006 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-097 | 戴眼镜也舒适的通勤头戴耳机 | fixture-001 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-098 | 不要堵耳的轻量耳夹 | fixture-019, fixture-020 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-099 | 高阻抗有线头戴室内听音 | fixture-024 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-100 | 五百元内小巧入耳主动降噪 | fixture-003 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-101 | 抗风噪户外通话无线耳机 | fixture-006, fixture-009 | ∅ | 0.000 | 0.000 | 0 | — |
| s8-102 | 半入耳无线通话，三百元内 | fixture-004, fixture-023 | ∅ | 0.000 | 0.000 | 0 | — |

### dense

| ID | Query | Expected | Retrieved | R@10 | nDCG@10 | Violations | Degraded |
|---|---|---|---|---:|---:|---:|---|
| lex-01 | Auralis Metro ANC 40 | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 0.500 | 0 | — |
| lex-02 | Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-001, fixture-018, fixture-014, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| lex-03 | MetroTone Buds N8 | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-021, fixture-011, fixture-010, fixture-014, fixture-001, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-04 | QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-016, fixture-023, fixture-022 | 1.000 | 1.000 | 0 | — |
| lex-05 | OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-016, fixture-013, fixture-012, fixture-007, fixture-022, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-06 | BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-003, fixture-016, fixture-006, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-07 | ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-015, fixture-018, fixture-001, fixture-023, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-08 | Auralis Pocket P4 ANC | fixture-015 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 0.631 | 0 | — |
| lex-09 | MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-021, fixture-011, fixture-012 | 1.000 | 1.000 | 0 | — |
| lex-10 | QuietArc Q7 Reference | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-006, fixture-007, fixture-019, fixture-012, fixture-023, fixture-022 | 1.000 | 0.631 | 0 | — |
| lex-11 | OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-022, fixture-023, fixture-012, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| lex-12 | ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-13 | Auralis | fixture-001, fixture-002, fixture-014, fixture-015, fixture-024 | fixture-014, fixture-024, fixture-015, fixture-001, fixture-002, fixture-022, fixture-004, fixture-023, fixture-013, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-14 | QuietArc | fixture-005, fixture-006, fixture-007, fixture-018 | fixture-018, fixture-005, fixture-007, fixture-006, fixture-012, fixture-022, fixture-023, fixture-013, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-15 | BoneWave | fixture-010, fixture-011, fixture-021 | fixture-011, fixture-021, fixture-010, fixture-016, fixture-017, fixture-003, fixture-004, fixture-007, fixture-012, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-16 | 主动降噪 | fixture-001, fixture-002, fixture-003, fixture-006, fixture-013, fixture-015, fixture-022 | fixture-002, fixture-013, fixture-015, fixture-018, fixture-001, fixture-016, fixture-017, fixture-014, fixture-005, fixture-004 | 0.571 | 0.692 | 0 | — |
| lex-17 | 骨传导 | fixture-010, fixture-011, fixture-021 | fixture-011, fixture-021, fixture-010, fixture-022, fixture-008, fixture-009, fixture-002, fixture-007, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-18 | 开放式 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-009, fixture-020, fixture-007, fixture-017, fixture-004, fixture-012, fixture-023, fixture-013 | 1.000 | 1.000 | 0 | — |
| lex-19 | 半入耳式 | fixture-004, fixture-017, fixture-023 | fixture-017, fixture-004, fixture-023, fixture-014, fixture-016, fixture-015, fixture-022, fixture-003, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-20 | 有线 | fixture-016, fixture-017, fixture-018, fixture-024 | fixture-024, fixture-016, fixture-017, fixture-018, fixture-012, fixture-023, fixture-008, fixture-020, fixture-013, fixture-022 | 1.000 | 1.000 | 0 | — |
| lex-21 | 通话 入耳式 | fixture-003, fixture-014, fixture-015, fixture-016, fixture-022 | fixture-022, fixture-023, fixture-015, fixture-007, fixture-017, fixture-016, fixture-014, fixture-004, fixture-005, fixture-020 | 0.800 | 0.743 | 0 | — |
| lex-22 | 通勤 | fixture-001, fixture-021 | fixture-021, fixture-006, fixture-001, fixture-005, fixture-020, fixture-023, fixture-015, fixture-022, fixture-014, fixture-002 | 1.000 | 0.920 | 0 | — |
| lex-23 | 办公 | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013, fixture-008, fixture-019, fixture-009, fixture-020, fixture-006, fixture-001, fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-24 | 户外 运动 | fixture-010 | fixture-010, fixture-003, fixture-015, fixture-013, fixture-014, fixture-005, fixture-004, fixture-006, fixture-008, fixture-019 | 1.000 | 1.000 | 0 | — |
| lex-25 | headphones | fixture-004, fixture-014, fixture-016, fixture-017, fixture-019, fixture-023 | fixture-017, fixture-016, fixture-004, fixture-023, fixture-014, fixture-019 | 1.000 | 1.000 | 0 | — |
| lex-26 | wireless | fixture-001, fixture-006 | fixture-001, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-27 | wireless | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 | — |
| lex-28 | microphone | fixture-012, fixture-013, fixture-022 | fixture-022, fixture-012, fixture-013 | 1.000 | 1.000 | 0 | — |
| lex-29 | headphones | fixture-014 | fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-30 | headphones | ∅ | ∅ | n/a | n/a | 0 | — |
| sem-01 | 地铁里想安静一点的通勤耳机 | fixture-001, fixture-002, fixture-006 | fixture-006, fixture-001, fixture-022, fixture-013, fixture-015, fixture-003, fixture-002 | 1.000 | 0.961 | 0 | — |
| sem-02 | 戴眼镜长时间听歌，不要太夹头 | fixture-001 | fixture-001, fixture-006, fixture-002, fixture-005, fixture-018, fixture-024 | 1.000 | 1.000 | 0 | — |
| sem-03 | 开会时人声清楚的办公耳机 | fixture-007, fixture-012, fixture-013 | fixture-003, fixture-007, fixture-012, fixture-013, fixture-018, fixture-002, fixture-005, fixture-006, fixture-008, fixture-009 | 1.000 | 0.733 | 0 | — |
| sem-04 | 跑步时还能听到周围环境 | fixture-008, fixture-009, fixture-010 | fixture-010, fixture-011, fixture-002, fixture-006, fixture-014, fixture-019, fixture-004, fixture-007, fixture-008, fixture-021 | 0.667 | 0.760 | 0 | — |
| sem-05 | 游泳训练用，防水要可靠 | fixture-011 | fixture-011, fixture-010, fixture-021 | 1.000 | 1.000 | 0 | — |
| sem-06 | 一周少充电的长续航头戴耳机 | fixture-001, fixture-002, fixture-006 | fixture-006, fixture-002, fixture-005, fixture-001 | 1.000 | 0.984 | 0 | — |
| sem-07 | 不想塞耳朵，还要能听见环境音 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-020, fixture-009 | 1.000 | 1.000 | 0 | — |
| sem-08 | 五百元内地铁通勤降噪入耳耳机 | fixture-003 | fixture-022, fixture-003 | 1.000 | 0.631 | 0 | — |
| sem-09 | 视频会议麦克风清晰，不要入耳式 | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013 | 1.000 | 1.000 | 0 | — |
| sem-10 | 户外雨天运动，防水耐用 | fixture-009, fixture-010, fixture-011 | fixture-010, fixture-011, fixture-014, fixture-004, fixture-008, fixture-019, fixture-009, fixture-020, fixture-023, fixture-021 | 1.000 | 0.952 | 0 | — |
| sem-11 | 便携小巧，适合每天随身带 | fixture-003, fixture-014 | fixture-014, fixture-003, fixture-022, fixture-015 | 1.000 | 1.000 | 0 | — |
| sem-12 | 喜欢人声靠前、低频适中的声音 | fixture-003 | fixture-003, fixture-018, fixture-002, fixture-001, fixture-007, fixture-015, fixture-009, fixture-023, fixture-006, fixture-013 | 1.000 | 1.000 | 0 | — |
| sem-13 | 旅行收纳方便、可以折叠的降噪耳机 | fixture-006 | fixture-006, fixture-002, fixture-001 | 1.000 | 1.000 | 0 | — |
| sem-14 | 高阻抗，适合室内安静听音 | fixture-018, fixture-024 | fixture-024, fixture-018 | 1.000 | 1.000 | 0 | — |
| sem-15 | 耳朵敏感，不堵耳而且轻量 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-009, fixture-020 | 1.000 | 1.000 | 0 | — |
| sem-16 | 便宜的有线耳塞，用来打电话 | fixture-016 | fixture-016 | 1.000 | 1.000 | 0 | — |
| sem-17 | 一百元内无线头戴主动降噪 | ∅ | ∅ | n/a | n/a | 0 | — |
| sem-18 | 户外通话时减少风噪 | fixture-006, fixture-009 | fixture-010, fixture-022, fixture-007, fixture-005, fixture-020, fixture-023, fixture-015, fixture-001, fixture-006, fixture-009 | 1.000 | 0.362 | 0 | — |
| s8-001 | Auralis Metro ANC 40 | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 0.500 | 0 | — |
| s8-002 | Auralis Auralis Metro ANC 40 | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-023 | 1.000 | 0.500 | 0 | — |
| s8-003 | Auralis Metro ANC 40 价格 899.00 CNY | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 0.500 | 0 | — |
| s8-004 | Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-001, fixture-018, fixture-014, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-005 | Auralis Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-004, fixture-016, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-006 | Auralis Studio ANC 55 价格 1299.00 CNY | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-018, fixture-001, fixture-014, fixture-017, fixture-005, fixture-016, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-007 | MetroTone Buds N8 | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-021, fixture-011, fixture-010, fixture-014, fixture-001, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-008 | MetroTone MetroTone Buds N8 | fixture-003 | fixture-016, fixture-003, fixture-017, fixture-004, fixture-011, fixture-021, fixture-010, fixture-001, fixture-014, fixture-007 | 1.000 | 0.631 | 0 | — |
| s8-009 | MetroTone Buds N8 价格 499.00 CNY | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-011, fixture-005, fixture-021, fixture-018, fixture-013, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-010 | MetroTone Air S2 | fixture-004 | fixture-004, fixture-017, fixture-016, fixture-003, fixture-021, fixture-011, fixture-001, fixture-010, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-011 | MetroTone MetroTone Air S2 | fixture-004 | fixture-004, fixture-017, fixture-016, fixture-003, fixture-011, fixture-021, fixture-010, fixture-001, fixture-007, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-012 | MetroTone Air S2 价格 199.00 CNY | fixture-004 | fixture-004, fixture-016, fixture-017, fixture-003, fixture-005, fixture-011, fixture-018, fixture-021, fixture-023, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-013 | QuietArc Q1 Lite | fixture-005 | fixture-005, fixture-018, fixture-007, fixture-006, fixture-012, fixture-023, fixture-013, fixture-022, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-014 | QuietArc QuietArc Q1 Lite | fixture-005 | fixture-018, fixture-005, fixture-007, fixture-006, fixture-012, fixture-023, fixture-022, fixture-013, fixture-016, fixture-017 | 1.000 | 0.631 | 0 | — |
| s8-015 | QuietArc Q1 Lite 价格 399.00 CNY | fixture-005 | fixture-005, fixture-018, fixture-007, fixture-006, fixture-012, fixture-013, fixture-023, fixture-016, fixture-004, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-016 | QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-016, fixture-023, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-017 | QuietArc QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-018, fixture-001, fixture-005, fixture-007, fixture-012, fixture-023, fixture-022, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-018 | QuietArc Q3 Travel 价格 699.00 CNY | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-023, fixture-013, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-019 | QuietArc Q5 Office | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-022, fixture-008, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-020 | QuietArc QuietArc Q5 Office | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-022, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-021 | QuietArc Q5 Office 价格 559.00 CNY | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-016, fixture-019, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-022 | OpenPath Loop 10 | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-021, fixture-013, fixture-004, fixture-012, fixture-007, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-023 | OpenPath OpenPath Loop 10 | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-007, fixture-013, fixture-012, fixture-021, fixture-004, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-024 | OpenPath Loop 10 价格 459.00 CNY | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-005, fixture-013, fixture-012, fixture-018, fixture-023, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-025 | OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-016, fixture-013, fixture-012, fixture-007, fixture-022, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-026 | OpenPath OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-007, fixture-013, fixture-012, fixture-016, fixture-024, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-027 | OpenPath Loop 14 价格 659.00 CNY | fixture-009 | fixture-009, fixture-008, fixture-019, fixture-020, fixture-005, fixture-012, fixture-013, fixture-018, fixture-016, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-028 | BoneWave Run B1 | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-016, fixture-003, fixture-017, fixture-004, fixture-012, fixture-007, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-029 | BoneWave BoneWave Run B1 | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-016, fixture-017, fixture-003, fixture-004, fixture-007, fixture-012, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-030 | BoneWave Run B1 价格 379.00 CNY | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-005, fixture-018, fixture-012, fixture-016, fixture-013, fixture-017, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-031 | BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-003, fixture-016, fixture-006, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-032 | BoneWave BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-016, fixture-003, fixture-007, fixture-012, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-033 | BoneWave Swim B2 价格 799.00 CNY | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-005, fixture-018, fixture-012, fixture-004, fixture-013, fixture-023, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-034 | ClearCall Work C20 | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-022, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-035 | ClearCall ClearCall Work C20 | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-022, fixture-018, fixture-005, fixture-024, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-036 | ClearCall Work C20 价格 329.00 CNY | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-005, fixture-018, fixture-022, fixture-024, fixture-017, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-037 | ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-015, fixture-018, fixture-001, fixture-023, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-038 | ClearCall ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-018, fixture-015, fixture-001, fixture-023, fixture-022, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-039 | ClearCall Work C40 ANC 价格 749.00 CNY | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-018, fixture-015, fixture-001, fixture-023, fixture-005, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-040 | Auralis Pocket P2 | fixture-014 | fixture-014, fixture-015, fixture-001, fixture-024, fixture-002, fixture-003, fixture-004, fixture-022, fixture-017, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-041 | Auralis Auralis Pocket P2 | fixture-014 | fixture-014, fixture-015, fixture-024, fixture-001, fixture-002, fixture-003, fixture-004, fixture-022, fixture-023, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-042 | Auralis Pocket P2 价格 259.00 CNY | fixture-014 | fixture-014, fixture-015, fixture-005, fixture-001, fixture-024, fixture-023, fixture-018, fixture-013, fixture-004, fixture-002 | 1.000 | 1.000 | 0 | — |
| s8-043 | Auralis Pocket P4 ANC | fixture-015 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 0.631 | 0 | — |
| s8-044 | Auralis Auralis Pocket P4 ANC | fixture-015 | fixture-002, fixture-015, fixture-001, fixture-014, fixture-013, fixture-018, fixture-017, fixture-004, fixture-016, fixture-005 | 1.000 | 0.631 | 0 | — |
| s8-045 | Auralis Pocket P4 ANC 价格 599.00 CNY | fixture-015 | fixture-002, fixture-015, fixture-013, fixture-018, fixture-001, fixture-014, fixture-005, fixture-016, fixture-017, fixture-004 | 1.000 | 0.631 | 0 | — |
| s8-046 | MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-021, fixture-011, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-047 | MetroTone MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-011, fixture-021, fixture-001, fixture-022, fixture-014, fixture-010 | 1.000 | 1.000 | 0 | — |
| s8-048 | MetroTone Cable M1 价格 99.00 CNY | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-018, fixture-005, fixture-012, fixture-011, fixture-013, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-049 | MetroTone Cable M3 | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-023, fixture-021, fixture-011 | 1.000 | 1.000 | 0 | — |
| s8-050 | MetroTone MetroTone Cable M3 | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-011, fixture-021, fixture-001, fixture-014, fixture-010, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-051 | MetroTone Cable M3 价格 129.00 CNY | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-012, fixture-013, fixture-023, fixture-011, fixture-018, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-052 | QuietArc Q7 Reference | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-006, fixture-007, fixture-019, fixture-012, fixture-023, fixture-022 | 1.000 | 0.631 | 0 | — |
| s8-053 | QuietArc QuietArc Q7 Reference | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-007, fixture-006, fixture-012, fixture-023, fixture-022, fixture-013 | 1.000 | 0.631 | 0 | — |
| s8-054 | QuietArc Q7 Reference 价格 999.00 CNY | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-006, fixture-007, fixture-012, fixture-019, fixture-016, fixture-013 | 1.000 | 0.631 | 0 | — |
| s8-055 | OpenPath Clip O2 | fixture-019 | fixture-019, fixture-020, fixture-008, fixture-009, fixture-024, fixture-013, fixture-018, fixture-023, fixture-012, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-056 | OpenPath OpenPath Clip O2 | fixture-019 | fixture-019, fixture-020, fixture-008, fixture-009, fixture-013, fixture-024, fixture-018, fixture-007, fixture-012, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-057 | OpenPath Clip O2 价格 299.00 CNY | fixture-019 | fixture-019, fixture-020, fixture-009, fixture-008, fixture-018, fixture-005, fixture-012, fixture-013, fixture-023, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-058 | OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-022, fixture-023, fixture-012, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-059 | OpenPath OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-012, fixture-007, fixture-022, fixture-023, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-060 | OpenPath Clip O5 价格 549.00 CNY | fixture-020 | fixture-020, fixture-019, fixture-009, fixture-008, fixture-013, fixture-012, fixture-005, fixture-018, fixture-023, fixture-015 | 1.000 | 1.000 | 0 | — |
| s8-061 | BoneWave City B3 | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-016, fixture-017, fixture-012, fixture-003, fixture-004, fixture-013, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-062 | BoneWave BoneWave City B3 | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-016, fixture-017, fixture-003, fixture-004, fixture-012, fixture-007, fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-063 | BoneWave City B3 价格 469.00 CNY | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-012, fixture-005, fixture-013, fixture-018, fixture-004, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-064 | ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-065 | ClearCall ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-066 | ClearCall Bud C8 价格 429.00 CNY | fixture-022 | fixture-012, fixture-013, fixture-022, fixture-023, fixture-018, fixture-005, fixture-024, fixture-017, fixture-011, fixture-019 | 1.000 | 0.500 | 0 | — |
| s8-067 | ClearCall Air C5 | fixture-023 | fixture-023, fixture-022, fixture-012, fixture-013, fixture-018, fixture-004, fixture-024, fixture-017, fixture-014, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-068 | ClearCall ClearCall Air C5 | fixture-023 | fixture-023, fixture-022, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-017, fixture-014, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-069 | ClearCall Air C5 价格 279.00 CNY | fixture-023 | fixture-023, fixture-012, fixture-013, fixture-018, fixture-005, fixture-022, fixture-004, fixture-017, fixture-014, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-070 | Auralis Studio Wired 80 | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-002, fixture-015, fixture-001, fixture-022, fixture-008 | 1.000 | 1.000 | 0 | — |
| s8-071 | Auralis Auralis Studio Wired 80 | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-015, fixture-002, fixture-001, fixture-022, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-072 | Auralis Studio Wired 80 价格 1599.00 CNY | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-015, fixture-002, fixture-001, fixture-005, fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-073 | Auralis Metro ANC 40 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-074 | Auralis Studio ANC 55 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-075 | MetroTone Buds N8 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-076 | MetroTone Air S2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-077 | QuietArc Q1 Lite | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-078 | QuietArc Q3 Travel | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-079 | QuietArc Q5 Office | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-080 | OpenPath Loop 10 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-081 | OpenPath Loop 14 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-082 | BoneWave Run B1 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-083 | BoneWave Swim B2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-084 | ClearCall Work C20 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-085 | ClearCall Work C40 ANC | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-086 | Auralis Pocket P2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-087 | Auralis Pocket P4 ANC | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-088 | MetroTone Cable M1 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-089 | MetroTone Cable M3 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-090 | QuietArc Q7 Reference | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-091 | 通勤地铁主动降噪，预算七百元 | fixture-003, fixture-006 | fixture-021, fixture-001, fixture-002, fixture-006, fixture-013, fixture-015, fixture-018, fixture-016, fixture-017, fixture-005 | 0.500 | 0.264 | 0 | — |
| s8-092 | 开放式跑步耳机，防水至少 IP55 | fixture-009 | fixture-010, fixture-008, fixture-019, fixture-009, fixture-020, fixture-011, fixture-014, fixture-004, fixture-023, fixture-015 | 1.000 | 0.431 | 0 | — |
| s8-093 | 游泳训练骨传导 IP68 | fixture-011 | fixture-011, fixture-010, fixture-021, fixture-022, fixture-014, fixture-004, fixture-009, fixture-019, fixture-008, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-094 | 办公室开会要杆式麦克风 | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013, fixture-022, fixture-005, fixture-020, fixture-023, fixture-015, fixture-001, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-095 | 百元以内有线入耳通话 | fixture-016 | fixture-016, fixture-017, fixture-024, fixture-022, fixture-023, fixture-015, fixture-007, fixture-014, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-096 | 长续航折叠旅行降噪头戴 | fixture-006 | fixture-006, fixture-002, fixture-009, fixture-005, fixture-001, fixture-013, fixture-015, fixture-016, fixture-014, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-097 | 戴眼镜也舒适的通勤头戴耳机 | fixture-001 | fixture-001, fixture-006, fixture-021, fixture-018, fixture-024, fixture-005, fixture-002, fixture-015, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-098 | 不要堵耳的轻量耳夹 | fixture-019, fixture-020 | fixture-008, fixture-019, fixture-004, fixture-014, fixture-012, fixture-009, fixture-020, fixture-003, fixture-017, fixture-022 | 1.000 | 0.591 | 0 | — |
| s8-099 | 高阻抗有线头戴室内听音 | fixture-024 | fixture-024, fixture-016, fixture-017, fixture-018, fixture-005, fixture-001, fixture-002, fixture-006, fixture-007, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-100 | 五百元内小巧入耳主动降噪 | fixture-003 | fixture-015, fixture-002, fixture-016, fixture-017, fixture-013, fixture-014, fixture-004, fixture-018, fixture-023, fixture-001 | 0.000 | 0.000 | 0 | — |
| s8-101 | 抗风噪户外通话无线耳机 | fixture-006, fixture-009 | fixture-010, fixture-022, fixture-005, fixture-020, fixture-007, fixture-023, fixture-015, fixture-001, fixture-014, fixture-009 | 0.500 | 0.177 | 0 | — |
| s8-102 | 半入耳无线通话，三百元内 | fixture-004, fixture-023 | fixture-023, fixture-022, fixture-004, fixture-015, fixture-017, fixture-014, fixture-005, fixture-020, fixture-007, fixture-003 | 1.000 | 0.920 | 0 | — |

### rrf

| ID | Query | Expected | Retrieved | R@10 | nDCG@10 | Violations | Degraded |
|---|---|---|---|---:|---:|---:|---|
| lex-01 | Auralis Metro ANC 40 | fixture-001 | fixture-001, fixture-002, fixture-015, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| lex-02 | Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-001, fixture-018, fixture-014, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| lex-03 | MetroTone Buds N8 | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-021, fixture-011, fixture-010, fixture-014, fixture-001, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-04 | QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-016, fixture-023, fixture-022 | 1.000 | 1.000 | 0 | — |
| lex-05 | OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-016, fixture-013, fixture-012, fixture-007, fixture-022, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-06 | BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-003, fixture-016, fixture-006, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-07 | ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-015, fixture-018, fixture-001, fixture-023, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-08 | Auralis Pocket P4 ANC | fixture-015 | fixture-015, fixture-002, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| lex-09 | MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-021, fixture-011, fixture-012 | 1.000 | 1.000 | 0 | — |
| lex-10 | QuietArc Q7 Reference | fixture-018 | fixture-018, fixture-003, fixture-002, fixture-005, fixture-006, fixture-007, fixture-019, fixture-012, fixture-023, fixture-022 | 1.000 | 1.000 | 0 | — |
| lex-11 | OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-022, fixture-023, fixture-012, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| lex-12 | ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-13 | Auralis | fixture-001, fixture-002, fixture-014, fixture-015, fixture-024 | fixture-014, fixture-001, fixture-015, fixture-024, fixture-002, fixture-022, fixture-004, fixture-023, fixture-013, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-14 | QuietArc | fixture-005, fixture-006, fixture-007, fixture-018 | fixture-005, fixture-018, fixture-006, fixture-007, fixture-012, fixture-022, fixture-023, fixture-013, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-15 | BoneWave | fixture-010, fixture-011, fixture-021 | fixture-021, fixture-011, fixture-010, fixture-016, fixture-017, fixture-003, fixture-004, fixture-007, fixture-012, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-16 | 主动降噪 | fixture-001, fixture-002, fixture-003, fixture-006, fixture-013, fixture-015, fixture-022 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-022, fixture-003, fixture-006, fixture-018, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-17 | 骨传导 | fixture-010, fixture-011, fixture-021 | fixture-021, fixture-011, fixture-010, fixture-022, fixture-008, fixture-009, fixture-002, fixture-007, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-18 | 开放式 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-019, fixture-008, fixture-020, fixture-009, fixture-007, fixture-017, fixture-004, fixture-012, fixture-023, fixture-013 | 1.000 | 1.000 | 0 | — |
| lex-19 | 半入耳式 | fixture-004, fixture-017, fixture-023 | fixture-023, fixture-017, fixture-004, fixture-014, fixture-016, fixture-015, fixture-022, fixture-003, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-20 | 有线 | fixture-016, fixture-017, fixture-018, fixture-024 | fixture-024, fixture-016, fixture-017, fixture-018, fixture-012, fixture-023, fixture-008, fixture-020, fixture-013, fixture-022 | 1.000 | 1.000 | 0 | — |
| lex-21 | 通话 入耳式 | fixture-003, fixture-014, fixture-015, fixture-016, fixture-022 | fixture-022, fixture-016, fixture-015, fixture-014, fixture-003, fixture-023, fixture-007, fixture-017, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| lex-22 | 通勤 | fixture-001, fixture-021 | fixture-021, fixture-001, fixture-006, fixture-005, fixture-020, fixture-023, fixture-015, fixture-022, fixture-014, fixture-002 | 1.000 | 1.000 | 0 | — |
| lex-23 | 办公 | fixture-007, fixture-012, fixture-013 | fixture-012, fixture-007, fixture-013, fixture-008, fixture-019, fixture-009, fixture-020, fixture-006, fixture-001, fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-24 | 户外 运动 | fixture-010 | fixture-010, fixture-003, fixture-015, fixture-013, fixture-014, fixture-005, fixture-004, fixture-006, fixture-008, fixture-019 | 1.000 | 1.000 | 0 | — |
| lex-25 | headphones | fixture-004, fixture-014, fixture-016, fixture-017, fixture-019, fixture-023 | fixture-014, fixture-017, fixture-023, fixture-016, fixture-004, fixture-019 | 1.000 | 1.000 | 0 | — |
| lex-26 | wireless | fixture-001, fixture-006 | fixture-001, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-27 | wireless | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 | — |
| lex-28 | microphone | fixture-012, fixture-013, fixture-022 | fixture-022, fixture-012, fixture-013 | 1.000 | 1.000 | 0 | — |
| lex-29 | headphones | fixture-014 | fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-30 | headphones | ∅ | ∅ | n/a | n/a | 0 | — |
| sem-01 | 地铁里想安静一点的通勤耳机 | fixture-001, fixture-002, fixture-006 | fixture-006, fixture-001, fixture-022, fixture-013, fixture-015, fixture-003, fixture-002 | 1.000 | 0.961 | 0 | — |
| sem-02 | 戴眼镜长时间听歌，不要太夹头 | fixture-001 | fixture-001, fixture-006, fixture-002, fixture-005, fixture-018, fixture-024 | 1.000 | 1.000 | 0 | — |
| sem-03 | 开会时人声清楚的办公耳机 | fixture-007, fixture-012, fixture-013 | fixture-003, fixture-007, fixture-012, fixture-013, fixture-018, fixture-002, fixture-005, fixture-006, fixture-008, fixture-009 | 1.000 | 0.733 | 0 | — |
| sem-04 | 跑步时还能听到周围环境 | fixture-008, fixture-009, fixture-010 | fixture-010, fixture-011, fixture-002, fixture-006, fixture-014, fixture-019, fixture-004, fixture-007, fixture-008, fixture-021 | 0.667 | 0.760 | 0 | — |
| sem-05 | 游泳训练用，防水要可靠 | fixture-011 | fixture-011, fixture-010, fixture-021 | 1.000 | 1.000 | 0 | — |
| sem-06 | 一周少充电的长续航头戴耳机 | fixture-001, fixture-002, fixture-006 | fixture-006, fixture-002, fixture-005, fixture-001 | 1.000 | 0.984 | 0 | — |
| sem-07 | 不想塞耳朵，还要能听见环境音 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-020, fixture-009 | 1.000 | 1.000 | 0 | — |
| sem-08 | 五百元内地铁通勤降噪入耳耳机 | fixture-003 | fixture-022, fixture-003 | 1.000 | 0.631 | 0 | — |
| sem-09 | 视频会议麦克风清晰，不要入耳式 | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013 | 1.000 | 1.000 | 0 | — |
| sem-10 | 户外雨天运动，防水耐用 | fixture-009, fixture-010, fixture-011 | fixture-010, fixture-011, fixture-014, fixture-004, fixture-008, fixture-019, fixture-009, fixture-020, fixture-023, fixture-021 | 1.000 | 0.952 | 0 | — |
| sem-11 | 便携小巧，适合每天随身带 | fixture-003, fixture-014 | fixture-014, fixture-003, fixture-022, fixture-015 | 1.000 | 1.000 | 0 | — |
| sem-12 | 喜欢人声靠前、低频适中的声音 | fixture-003 | fixture-003, fixture-018, fixture-002, fixture-001, fixture-007, fixture-015, fixture-009, fixture-023, fixture-006, fixture-013 | 1.000 | 1.000 | 0 | — |
| sem-13 | 旅行收纳方便、可以折叠的降噪耳机 | fixture-006 | fixture-006, fixture-002, fixture-001 | 1.000 | 1.000 | 0 | — |
| sem-14 | 高阻抗，适合室内安静听音 | fixture-018, fixture-024 | fixture-024, fixture-018 | 1.000 | 1.000 | 0 | — |
| sem-15 | 耳朵敏感，不堵耳而且轻量 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-009, fixture-020 | 1.000 | 1.000 | 0 | — |
| sem-16 | 便宜的有线耳塞，用来打电话 | fixture-016 | fixture-016 | 1.000 | 1.000 | 0 | — |
| sem-17 | 一百元内无线头戴主动降噪 | ∅ | ∅ | n/a | n/a | 0 | — |
| sem-18 | 户外通话时减少风噪 | fixture-006, fixture-009 | fixture-010, fixture-022, fixture-007, fixture-005, fixture-020, fixture-023, fixture-015, fixture-001, fixture-006, fixture-009 | 1.000 | 0.362 | 0 | — |
| s8-001 | Auralis Metro ANC 40 | fixture-001 | fixture-001, fixture-002, fixture-015, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-002 | Auralis Auralis Metro ANC 40 | fixture-001 | fixture-001, fixture-002, fixture-015, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-003 | Auralis Metro ANC 40 价格 899.00 CNY | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 0.500 | 0 | — |
| s8-004 | Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-001, fixture-018, fixture-014, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-005 | Auralis Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-004, fixture-016, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-006 | Auralis Studio ANC 55 价格 1299.00 CNY | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-018, fixture-001, fixture-014, fixture-017, fixture-005, fixture-016, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-007 | MetroTone Buds N8 | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-021, fixture-011, fixture-010, fixture-014, fixture-001, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-008 | MetroTone MetroTone Buds N8 | fixture-003 | fixture-003, fixture-016, fixture-017, fixture-004, fixture-011, fixture-021, fixture-010, fixture-001, fixture-014, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-009 | MetroTone Buds N8 价格 499.00 CNY | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-011, fixture-005, fixture-021, fixture-018, fixture-013, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-010 | MetroTone Air S2 | fixture-004 | fixture-004, fixture-017, fixture-016, fixture-003, fixture-021, fixture-011, fixture-001, fixture-010, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-011 | MetroTone MetroTone Air S2 | fixture-004 | fixture-004, fixture-017, fixture-016, fixture-003, fixture-011, fixture-021, fixture-010, fixture-001, fixture-007, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-012 | MetroTone Air S2 价格 199.00 CNY | fixture-004 | fixture-004, fixture-016, fixture-017, fixture-003, fixture-005, fixture-011, fixture-018, fixture-021, fixture-023, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-013 | QuietArc Q1 Lite | fixture-005 | fixture-005, fixture-018, fixture-007, fixture-006, fixture-012, fixture-023, fixture-013, fixture-022, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-014 | QuietArc QuietArc Q1 Lite | fixture-005 | fixture-005, fixture-018, fixture-007, fixture-006, fixture-012, fixture-023, fixture-022, fixture-013, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-015 | QuietArc Q1 Lite 价格 399.00 CNY | fixture-005 | fixture-005, fixture-018, fixture-007, fixture-006, fixture-012, fixture-013, fixture-023, fixture-016, fixture-004, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-016 | QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-016, fixture-023, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-017 | QuietArc QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-018, fixture-001, fixture-005, fixture-007, fixture-012, fixture-023, fixture-022, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-018 | QuietArc Q3 Travel 价格 699.00 CNY | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-023, fixture-013, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-019 | QuietArc Q5 Office | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-022, fixture-008, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-020 | QuietArc QuietArc Q5 Office | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-022, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-021 | QuietArc Q5 Office 价格 559.00 CNY | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-016, fixture-019, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-022 | OpenPath Loop 10 | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-021, fixture-013, fixture-004, fixture-012, fixture-007, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-023 | OpenPath OpenPath Loop 10 | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-007, fixture-013, fixture-012, fixture-021, fixture-004, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-024 | OpenPath Loop 10 价格 459.00 CNY | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-005, fixture-013, fixture-012, fixture-018, fixture-023, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-025 | OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-016, fixture-013, fixture-012, fixture-007, fixture-022, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-026 | OpenPath OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-007, fixture-013, fixture-012, fixture-016, fixture-024, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-027 | OpenPath Loop 14 价格 659.00 CNY | fixture-009 | fixture-009, fixture-008, fixture-019, fixture-020, fixture-005, fixture-012, fixture-013, fixture-018, fixture-016, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-028 | BoneWave Run B1 | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-016, fixture-003, fixture-017, fixture-004, fixture-012, fixture-007, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-029 | BoneWave BoneWave Run B1 | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-016, fixture-017, fixture-003, fixture-004, fixture-007, fixture-012, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-030 | BoneWave Run B1 价格 379.00 CNY | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-005, fixture-018, fixture-012, fixture-016, fixture-013, fixture-017, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-031 | BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-003, fixture-016, fixture-006, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-032 | BoneWave BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-016, fixture-003, fixture-007, fixture-012, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-033 | BoneWave Swim B2 价格 799.00 CNY | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-005, fixture-018, fixture-012, fixture-004, fixture-013, fixture-023, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-034 | ClearCall Work C20 | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-022, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-035 | ClearCall ClearCall Work C20 | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-022, fixture-018, fixture-005, fixture-024, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-036 | ClearCall Work C20 价格 329.00 CNY | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-005, fixture-018, fixture-022, fixture-024, fixture-017, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-037 | ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-015, fixture-018, fixture-001, fixture-023, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-038 | ClearCall ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-018, fixture-015, fixture-001, fixture-023, fixture-022, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-039 | ClearCall Work C40 ANC 价格 749.00 CNY | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-018, fixture-015, fixture-001, fixture-023, fixture-005, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-040 | Auralis Pocket P2 | fixture-014 | fixture-014, fixture-015, fixture-001, fixture-024, fixture-002, fixture-003, fixture-004, fixture-022, fixture-017, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-041 | Auralis Auralis Pocket P2 | fixture-014 | fixture-014, fixture-015, fixture-024, fixture-001, fixture-002, fixture-003, fixture-004, fixture-022, fixture-023, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-042 | Auralis Pocket P2 价格 259.00 CNY | fixture-014 | fixture-014, fixture-015, fixture-005, fixture-001, fixture-024, fixture-023, fixture-018, fixture-013, fixture-004, fixture-002 | 1.000 | 1.000 | 0 | — |
| s8-043 | Auralis Pocket P4 ANC | fixture-015 | fixture-015, fixture-002, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-044 | Auralis Auralis Pocket P4 ANC | fixture-015 | fixture-015, fixture-002, fixture-001, fixture-014, fixture-013, fixture-018, fixture-017, fixture-004, fixture-016, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-045 | Auralis Pocket P4 ANC 价格 599.00 CNY | fixture-015 | fixture-002, fixture-015, fixture-013, fixture-018, fixture-001, fixture-014, fixture-005, fixture-016, fixture-017, fixture-004 | 1.000 | 0.631 | 0 | — |
| s8-046 | MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-021, fixture-011, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-047 | MetroTone MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-011, fixture-021, fixture-001, fixture-022, fixture-014, fixture-010 | 1.000 | 1.000 | 0 | — |
| s8-048 | MetroTone Cable M1 价格 99.00 CNY | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-018, fixture-005, fixture-012, fixture-011, fixture-013, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-049 | MetroTone Cable M3 | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-023, fixture-021, fixture-011 | 1.000 | 1.000 | 0 | — |
| s8-050 | MetroTone MetroTone Cable M3 | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-011, fixture-021, fixture-001, fixture-014, fixture-010, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-051 | MetroTone Cable M3 价格 129.00 CNY | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-012, fixture-013, fixture-023, fixture-011, fixture-018, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-052 | QuietArc Q7 Reference | fixture-018 | fixture-018, fixture-003, fixture-002, fixture-005, fixture-006, fixture-007, fixture-019, fixture-012, fixture-023, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-053 | QuietArc QuietArc Q7 Reference | fixture-018 | fixture-018, fixture-003, fixture-002, fixture-005, fixture-007, fixture-006, fixture-012, fixture-023, fixture-022, fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-054 | QuietArc Q7 Reference 价格 999.00 CNY | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-006, fixture-007, fixture-012, fixture-019, fixture-016, fixture-013 | 1.000 | 0.631 | 0 | — |
| s8-055 | OpenPath Clip O2 | fixture-019 | fixture-019, fixture-020, fixture-008, fixture-009, fixture-024, fixture-013, fixture-018, fixture-023, fixture-012, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-056 | OpenPath OpenPath Clip O2 | fixture-019 | fixture-019, fixture-020, fixture-008, fixture-009, fixture-013, fixture-024, fixture-018, fixture-007, fixture-012, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-057 | OpenPath Clip O2 价格 299.00 CNY | fixture-019 | fixture-019, fixture-020, fixture-009, fixture-008, fixture-018, fixture-005, fixture-012, fixture-013, fixture-023, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-058 | OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-022, fixture-023, fixture-012, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-059 | OpenPath OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-012, fixture-007, fixture-022, fixture-023, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-060 | OpenPath Clip O5 价格 549.00 CNY | fixture-020 | fixture-020, fixture-019, fixture-009, fixture-008, fixture-013, fixture-012, fixture-005, fixture-018, fixture-023, fixture-015 | 1.000 | 1.000 | 0 | — |
| s8-061 | BoneWave City B3 | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-016, fixture-017, fixture-012, fixture-003, fixture-004, fixture-013, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-062 | BoneWave BoneWave City B3 | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-016, fixture-017, fixture-003, fixture-004, fixture-012, fixture-007, fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-063 | BoneWave City B3 价格 469.00 CNY | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-012, fixture-005, fixture-013, fixture-018, fixture-004, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-064 | ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-065 | ClearCall ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-066 | ClearCall Bud C8 价格 429.00 CNY | fixture-022 | fixture-012, fixture-013, fixture-022, fixture-023, fixture-018, fixture-005, fixture-024, fixture-017, fixture-011, fixture-019 | 1.000 | 0.500 | 0 | — |
| s8-067 | ClearCall Air C5 | fixture-023 | fixture-023, fixture-022, fixture-012, fixture-013, fixture-018, fixture-004, fixture-024, fixture-017, fixture-014, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-068 | ClearCall ClearCall Air C5 | fixture-023 | fixture-023, fixture-022, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-017, fixture-014, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-069 | ClearCall Air C5 价格 279.00 CNY | fixture-023 | fixture-023, fixture-012, fixture-013, fixture-018, fixture-005, fixture-022, fixture-004, fixture-017, fixture-014, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-070 | Auralis Studio Wired 80 | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-002, fixture-015, fixture-001, fixture-022, fixture-008 | 1.000 | 1.000 | 0 | — |
| s8-071 | Auralis Auralis Studio Wired 80 | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-015, fixture-002, fixture-001, fixture-022, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-072 | Auralis Studio Wired 80 价格 1599.00 CNY | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-015, fixture-002, fixture-001, fixture-005, fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-073 | Auralis Metro ANC 40 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-074 | Auralis Studio ANC 55 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-075 | MetroTone Buds N8 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-076 | MetroTone Air S2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-077 | QuietArc Q1 Lite | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-078 | QuietArc Q3 Travel | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-079 | QuietArc Q5 Office | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-080 | OpenPath Loop 10 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-081 | OpenPath Loop 14 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-082 | BoneWave Run B1 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-083 | BoneWave Swim B2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-084 | ClearCall Work C20 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-085 | ClearCall Work C40 ANC | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-086 | Auralis Pocket P2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-087 | Auralis Pocket P4 ANC | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-088 | MetroTone Cable M1 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-089 | MetroTone Cable M3 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-090 | QuietArc Q7 Reference | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-091 | 通勤地铁主动降噪，预算七百元 | fixture-003, fixture-006 | fixture-021, fixture-001, fixture-002, fixture-006, fixture-013, fixture-015, fixture-018, fixture-016, fixture-017, fixture-005 | 0.500 | 0.264 | 0 | — |
| s8-092 | 开放式跑步耳机，防水至少 IP55 | fixture-009 | fixture-010, fixture-008, fixture-019, fixture-009, fixture-020, fixture-011, fixture-014, fixture-004, fixture-023, fixture-015 | 1.000 | 0.431 | 0 | — |
| s8-093 | 游泳训练骨传导 IP68 | fixture-011 | fixture-011, fixture-010, fixture-021, fixture-022, fixture-014, fixture-004, fixture-009, fixture-019, fixture-008, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-094 | 办公室开会要杆式麦克风 | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013, fixture-022, fixture-005, fixture-020, fixture-023, fixture-015, fixture-001, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-095 | 百元以内有线入耳通话 | fixture-016 | fixture-016, fixture-017, fixture-024, fixture-022, fixture-023, fixture-015, fixture-007, fixture-014, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-096 | 长续航折叠旅行降噪头戴 | fixture-006 | fixture-006, fixture-002, fixture-009, fixture-005, fixture-001, fixture-013, fixture-015, fixture-016, fixture-014, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-097 | 戴眼镜也舒适的通勤头戴耳机 | fixture-001 | fixture-001, fixture-006, fixture-021, fixture-018, fixture-024, fixture-005, fixture-002, fixture-015, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-098 | 不要堵耳的轻量耳夹 | fixture-019, fixture-020 | fixture-008, fixture-019, fixture-004, fixture-014, fixture-012, fixture-009, fixture-020, fixture-003, fixture-017, fixture-022 | 1.000 | 0.591 | 0 | — |
| s8-099 | 高阻抗有线头戴室内听音 | fixture-024 | fixture-024, fixture-016, fixture-017, fixture-018, fixture-005, fixture-001, fixture-002, fixture-006, fixture-007, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-100 | 五百元内小巧入耳主动降噪 | fixture-003 | fixture-015, fixture-002, fixture-016, fixture-017, fixture-013, fixture-014, fixture-004, fixture-018, fixture-023, fixture-001 | 0.000 | 0.000 | 0 | — |
| s8-101 | 抗风噪户外通话无线耳机 | fixture-006, fixture-009 | fixture-010, fixture-022, fixture-005, fixture-020, fixture-007, fixture-023, fixture-015, fixture-001, fixture-014, fixture-009 | 0.500 | 0.177 | 0 | — |
| s8-102 | 半入耳无线通话，三百元内 | fixture-004, fixture-023 | fixture-023, fixture-022, fixture-004, fixture-015, fixture-017, fixture-014, fixture-005, fixture-020, fixture-007, fixture-003 | 1.000 | 0.920 | 0 | — |

### rerank

| ID | Query | Expected | Retrieved | R@10 | nDCG@10 | Violations | Degraded |
|---|---|---|---|---:|---:|---:|---|
| lex-01 | Auralis Metro ANC 40 | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 0.500 | 0 | — |
| lex-02 | Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-001, fixture-018, fixture-014, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| lex-03 | MetroTone Buds N8 | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-021, fixture-011, fixture-010, fixture-014, fixture-001, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-04 | QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-016, fixture-023, fixture-022 | 1.000 | 1.000 | 0 | — |
| lex-05 | OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-016, fixture-013, fixture-012, fixture-007, fixture-022, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-06 | BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-003, fixture-016, fixture-006, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-07 | ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-015, fixture-018, fixture-001, fixture-023, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-08 | Auralis Pocket P4 ANC | fixture-015 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 0.631 | 0 | — |
| lex-09 | MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-021, fixture-011, fixture-012 | 1.000 | 1.000 | 0 | — |
| lex-10 | QuietArc Q7 Reference | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-006, fixture-007, fixture-019, fixture-012, fixture-023, fixture-022 | 1.000 | 0.631 | 0 | — |
| lex-11 | OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-022, fixture-023, fixture-012, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| lex-12 | ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-13 | Auralis | fixture-001, fixture-002, fixture-014, fixture-015, fixture-024 | fixture-014, fixture-024, fixture-015, fixture-001, fixture-002, fixture-022, fixture-004, fixture-023, fixture-013, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-14 | QuietArc | fixture-005, fixture-006, fixture-007, fixture-018 | fixture-018, fixture-005, fixture-007, fixture-006, fixture-012, fixture-022, fixture-023, fixture-013, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-15 | BoneWave | fixture-010, fixture-011, fixture-021 | fixture-011, fixture-021, fixture-010, fixture-016, fixture-017, fixture-003, fixture-004, fixture-007, fixture-012, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-16 | 主动降噪 | fixture-001, fixture-002, fixture-003, fixture-006, fixture-013, fixture-015, fixture-022 | fixture-002, fixture-013, fixture-015, fixture-018, fixture-001, fixture-016, fixture-017, fixture-014, fixture-005, fixture-004 | 0.571 | 0.692 | 0 | — |
| lex-17 | 骨传导 | fixture-010, fixture-011, fixture-021 | fixture-011, fixture-021, fixture-010, fixture-022, fixture-008, fixture-009, fixture-002, fixture-007, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| lex-18 | 开放式 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-009, fixture-020, fixture-007, fixture-017, fixture-004, fixture-012, fixture-023, fixture-013 | 1.000 | 1.000 | 0 | — |
| lex-19 | 半入耳式 | fixture-004, fixture-017, fixture-023 | fixture-017, fixture-004, fixture-023, fixture-014, fixture-016, fixture-015, fixture-022, fixture-003, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| lex-20 | 有线 | fixture-016, fixture-017, fixture-018, fixture-024 | fixture-024, fixture-016, fixture-017, fixture-018, fixture-012, fixture-023, fixture-008, fixture-020, fixture-013, fixture-022 | 1.000 | 1.000 | 0 | — |
| lex-21 | 通话 入耳式 | fixture-003, fixture-014, fixture-015, fixture-016, fixture-022 | fixture-022, fixture-023, fixture-015, fixture-007, fixture-017, fixture-016, fixture-014, fixture-004, fixture-005, fixture-020 | 0.800 | 0.743 | 0 | — |
| lex-22 | 通勤 | fixture-001, fixture-021 | fixture-021, fixture-006, fixture-001, fixture-005, fixture-020, fixture-023, fixture-015, fixture-022, fixture-014, fixture-002 | 1.000 | 0.920 | 0 | — |
| lex-23 | 办公 | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013, fixture-008, fixture-019, fixture-009, fixture-020, fixture-006, fixture-001, fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-24 | 户外 运动 | fixture-010 | fixture-010, fixture-003, fixture-015, fixture-013, fixture-014, fixture-005, fixture-004, fixture-006, fixture-008, fixture-019 | 1.000 | 1.000 | 0 | — |
| lex-25 | headphones | fixture-004, fixture-014, fixture-016, fixture-017, fixture-019, fixture-023 | fixture-017, fixture-016, fixture-004, fixture-023, fixture-014, fixture-019 | 1.000 | 1.000 | 0 | — |
| lex-26 | wireless | fixture-001, fixture-006 | fixture-001, fixture-006 | 1.000 | 1.000 | 0 | — |
| lex-27 | wireless | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 | — |
| lex-28 | microphone | fixture-012, fixture-013, fixture-022 | fixture-022, fixture-012, fixture-013 | 1.000 | 1.000 | 0 | — |
| lex-29 | headphones | fixture-014 | fixture-014 | 1.000 | 1.000 | 0 | — |
| lex-30 | headphones | ∅ | ∅ | n/a | n/a | 0 | — |
| sem-01 | 地铁里想安静一点的通勤耳机 | fixture-001, fixture-002, fixture-006 | fixture-006, fixture-001, fixture-022, fixture-013, fixture-015, fixture-003, fixture-002 | 1.000 | 0.961 | 0 | — |
| sem-02 | 戴眼镜长时间听歌，不要太夹头 | fixture-001 | fixture-001, fixture-006, fixture-002, fixture-005, fixture-018, fixture-024 | 1.000 | 1.000 | 0 | — |
| sem-03 | 开会时人声清楚的办公耳机 | fixture-007, fixture-012, fixture-013 | fixture-003, fixture-007, fixture-012, fixture-013, fixture-018, fixture-002, fixture-005, fixture-006, fixture-008, fixture-009 | 1.000 | 0.733 | 0 | — |
| sem-04 | 跑步时还能听到周围环境 | fixture-008, fixture-009, fixture-010 | fixture-010, fixture-011, fixture-002, fixture-006, fixture-014, fixture-019, fixture-004, fixture-007, fixture-008, fixture-021 | 0.667 | 0.760 | 0 | — |
| sem-05 | 游泳训练用，防水要可靠 | fixture-011 | fixture-011, fixture-010, fixture-021 | 1.000 | 1.000 | 0 | — |
| sem-06 | 一周少充电的长续航头戴耳机 | fixture-001, fixture-002, fixture-006 | fixture-006, fixture-002, fixture-005, fixture-001 | 1.000 | 0.984 | 0 | — |
| sem-07 | 不想塞耳朵，还要能听见环境音 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-020, fixture-009 | 1.000 | 1.000 | 0 | — |
| sem-08 | 五百元内地铁通勤降噪入耳耳机 | fixture-003 | fixture-022, fixture-003 | 1.000 | 0.631 | 0 | — |
| sem-09 | 视频会议麦克风清晰，不要入耳式 | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013 | 1.000 | 1.000 | 0 | — |
| sem-10 | 户外雨天运动，防水耐用 | fixture-009, fixture-010, fixture-011 | fixture-010, fixture-011, fixture-014, fixture-004, fixture-008, fixture-019, fixture-009, fixture-020, fixture-023, fixture-021 | 1.000 | 0.952 | 0 | — |
| sem-11 | 便携小巧，适合每天随身带 | fixture-003, fixture-014 | fixture-014, fixture-003, fixture-022, fixture-015 | 1.000 | 1.000 | 0 | — |
| sem-12 | 喜欢人声靠前、低频适中的声音 | fixture-003 | fixture-003, fixture-018, fixture-002, fixture-001, fixture-007, fixture-015, fixture-009, fixture-023, fixture-006, fixture-013 | 1.000 | 1.000 | 0 | — |
| sem-13 | 旅行收纳方便、可以折叠的降噪耳机 | fixture-006 | fixture-006, fixture-002, fixture-001 | 1.000 | 1.000 | 0 | — |
| sem-14 | 高阻抗，适合室内安静听音 | fixture-018, fixture-024 | fixture-024, fixture-018 | 1.000 | 1.000 | 0 | — |
| sem-15 | 耳朵敏感，不堵耳而且轻量 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-009, fixture-020 | 1.000 | 1.000 | 0 | — |
| sem-16 | 便宜的有线耳塞，用来打电话 | fixture-016 | fixture-016 | 1.000 | 1.000 | 0 | — |
| sem-17 | 一百元内无线头戴主动降噪 | ∅ | ∅ | n/a | n/a | 0 | — |
| sem-18 | 户外通话时减少风噪 | fixture-006, fixture-009 | fixture-010, fixture-022, fixture-007, fixture-005, fixture-020, fixture-023, fixture-015, fixture-001, fixture-006, fixture-009 | 1.000 | 0.362 | 0 | — |
| s8-001 | Auralis Metro ANC 40 | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 0.500 | 0 | — |
| s8-002 | Auralis Auralis Metro ANC 40 | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-023 | 1.000 | 0.500 | 0 | — |
| s8-003 | Auralis Metro ANC 40 价格 899.00 CNY | fixture-001 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-018, fixture-014, fixture-016, fixture-017, fixture-004, fixture-005 | 1.000 | 0.500 | 0 | — |
| s8-004 | Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-001, fixture-018, fixture-014, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-005 | Auralis Auralis Studio ANC 55 | fixture-002 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-004, fixture-016, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-006 | Auralis Studio ANC 55 价格 1299.00 CNY | fixture-002 | fixture-002, fixture-015, fixture-013, fixture-018, fixture-001, fixture-014, fixture-017, fixture-005, fixture-016, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-007 | MetroTone Buds N8 | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-021, fixture-011, fixture-010, fixture-014, fixture-001, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-008 | MetroTone MetroTone Buds N8 | fixture-003 | fixture-016, fixture-003, fixture-017, fixture-004, fixture-011, fixture-021, fixture-010, fixture-001, fixture-014, fixture-007 | 1.000 | 0.631 | 0 | — |
| s8-009 | MetroTone Buds N8 价格 499.00 CNY | fixture-003 | fixture-003, fixture-004, fixture-016, fixture-017, fixture-011, fixture-005, fixture-021, fixture-018, fixture-013, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-010 | MetroTone Air S2 | fixture-004 | fixture-004, fixture-017, fixture-016, fixture-003, fixture-021, fixture-011, fixture-001, fixture-010, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-011 | MetroTone MetroTone Air S2 | fixture-004 | fixture-004, fixture-017, fixture-016, fixture-003, fixture-011, fixture-021, fixture-010, fixture-001, fixture-007, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-012 | MetroTone Air S2 价格 199.00 CNY | fixture-004 | fixture-004, fixture-016, fixture-017, fixture-003, fixture-005, fixture-011, fixture-018, fixture-021, fixture-023, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-013 | QuietArc Q1 Lite | fixture-005 | fixture-005, fixture-018, fixture-007, fixture-006, fixture-012, fixture-023, fixture-013, fixture-022, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-014 | QuietArc QuietArc Q1 Lite | fixture-005 | fixture-018, fixture-005, fixture-007, fixture-006, fixture-012, fixture-023, fixture-022, fixture-013, fixture-016, fixture-017 | 1.000 | 0.631 | 0 | — |
| s8-015 | QuietArc Q1 Lite 价格 399.00 CNY | fixture-005 | fixture-005, fixture-018, fixture-007, fixture-006, fixture-012, fixture-013, fixture-023, fixture-016, fixture-004, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-016 | QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-016, fixture-023, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-017 | QuietArc QuietArc Q3 Travel | fixture-006 | fixture-006, fixture-021, fixture-018, fixture-001, fixture-005, fixture-007, fixture-012, fixture-023, fixture-022, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-018 | QuietArc Q3 Travel 价格 699.00 CNY | fixture-006 | fixture-006, fixture-021, fixture-001, fixture-018, fixture-005, fixture-007, fixture-012, fixture-023, fixture-013, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-019 | QuietArc Q5 Office | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-022, fixture-008, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-020 | QuietArc QuietArc Q5 Office | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-022, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-021 | QuietArc Q5 Office 价格 559.00 CNY | fixture-007 | fixture-007, fixture-012, fixture-013, fixture-018, fixture-005, fixture-006, fixture-023, fixture-016, fixture-019, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-022 | OpenPath Loop 10 | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-021, fixture-013, fixture-004, fixture-012, fixture-007, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-023 | OpenPath OpenPath Loop 10 | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-007, fixture-013, fixture-012, fixture-021, fixture-004, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-024 | OpenPath Loop 10 价格 459.00 CNY | fixture-008 | fixture-008, fixture-009, fixture-020, fixture-019, fixture-005, fixture-013, fixture-012, fixture-018, fixture-023, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-025 | OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-016, fixture-013, fixture-012, fixture-007, fixture-022, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-026 | OpenPath OpenPath Loop 14 | fixture-009 | fixture-009, fixture-008, fixture-020, fixture-019, fixture-007, fixture-013, fixture-012, fixture-016, fixture-024, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-027 | OpenPath Loop 14 价格 659.00 CNY | fixture-009 | fixture-009, fixture-008, fixture-019, fixture-020, fixture-005, fixture-012, fixture-013, fixture-018, fixture-016, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-028 | BoneWave Run B1 | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-016, fixture-003, fixture-017, fixture-004, fixture-012, fixture-007, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-029 | BoneWave BoneWave Run B1 | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-016, fixture-017, fixture-003, fixture-004, fixture-007, fixture-012, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-030 | BoneWave Run B1 价格 379.00 CNY | fixture-010 | fixture-010, fixture-011, fixture-021, fixture-005, fixture-018, fixture-012, fixture-016, fixture-013, fixture-017, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-031 | BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-003, fixture-016, fixture-006, fixture-012, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-032 | BoneWave BoneWave Swim B2 | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-004, fixture-017, fixture-016, fixture-003, fixture-007, fixture-012, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-033 | BoneWave Swim B2 价格 799.00 CNY | fixture-011 | fixture-011, fixture-021, fixture-010, fixture-005, fixture-018, fixture-012, fixture-004, fixture-013, fixture-023, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-034 | ClearCall Work C20 | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-022, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-035 | ClearCall ClearCall Work C20 | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-022, fixture-018, fixture-005, fixture-024, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-036 | ClearCall Work C20 价格 329.00 CNY | fixture-012 | fixture-012, fixture-007, fixture-013, fixture-023, fixture-005, fixture-018, fixture-022, fixture-024, fixture-017, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-037 | ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-015, fixture-018, fixture-001, fixture-023, fixture-016, fixture-014 | 1.000 | 1.000 | 0 | — |
| s8-038 | ClearCall ClearCall Work C40 ANC | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-018, fixture-015, fixture-001, fixture-023, fixture-022, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-039 | ClearCall Work C40 ANC 价格 749.00 CNY | fixture-013 | fixture-013, fixture-012, fixture-007, fixture-002, fixture-018, fixture-015, fixture-001, fixture-023, fixture-005, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-040 | Auralis Pocket P2 | fixture-014 | fixture-014, fixture-015, fixture-001, fixture-024, fixture-002, fixture-003, fixture-004, fixture-022, fixture-017, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-041 | Auralis Auralis Pocket P2 | fixture-014 | fixture-014, fixture-015, fixture-024, fixture-001, fixture-002, fixture-003, fixture-004, fixture-022, fixture-023, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-042 | Auralis Pocket P2 价格 259.00 CNY | fixture-014 | fixture-014, fixture-015, fixture-005, fixture-001, fixture-024, fixture-023, fixture-018, fixture-013, fixture-004, fixture-002 | 1.000 | 1.000 | 0 | — |
| s8-043 | Auralis Pocket P4 ANC | fixture-015 | fixture-002, fixture-015, fixture-001, fixture-013, fixture-014, fixture-018, fixture-017, fixture-016, fixture-004, fixture-005 | 1.000 | 0.631 | 0 | — |
| s8-044 | Auralis Auralis Pocket P4 ANC | fixture-015 | fixture-002, fixture-015, fixture-001, fixture-014, fixture-013, fixture-018, fixture-017, fixture-004, fixture-016, fixture-005 | 1.000 | 0.631 | 0 | — |
| s8-045 | Auralis Pocket P4 ANC 价格 599.00 CNY | fixture-015 | fixture-002, fixture-015, fixture-013, fixture-018, fixture-001, fixture-014, fixture-005, fixture-016, fixture-017, fixture-004 | 1.000 | 0.631 | 0 | — |
| s8-046 | MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-021, fixture-011, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-047 | MetroTone MetroTone Cable M1 | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-011, fixture-021, fixture-001, fixture-022, fixture-014, fixture-010 | 1.000 | 1.000 | 0 | — |
| s8-048 | MetroTone Cable M1 价格 99.00 CNY | fixture-016 | fixture-016, fixture-017, fixture-004, fixture-003, fixture-018, fixture-005, fixture-012, fixture-011, fixture-013, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-049 | MetroTone Cable M3 | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-022, fixture-001, fixture-014, fixture-023, fixture-021, fixture-011 | 1.000 | 1.000 | 0 | — |
| s8-050 | MetroTone MetroTone Cable M3 | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-011, fixture-021, fixture-001, fixture-014, fixture-010, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-051 | MetroTone Cable M3 价格 129.00 CNY | fixture-017 | fixture-017, fixture-016, fixture-004, fixture-003, fixture-012, fixture-013, fixture-023, fixture-011, fixture-018, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-052 | QuietArc Q7 Reference | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-006, fixture-007, fixture-019, fixture-012, fixture-023, fixture-022 | 1.000 | 0.631 | 0 | — |
| s8-053 | QuietArc QuietArc Q7 Reference | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-007, fixture-006, fixture-012, fixture-023, fixture-022, fixture-013 | 1.000 | 0.631 | 0 | — |
| s8-054 | QuietArc Q7 Reference 价格 999.00 CNY | fixture-018 | fixture-003, fixture-018, fixture-002, fixture-005, fixture-006, fixture-007, fixture-012, fixture-019, fixture-016, fixture-013 | 1.000 | 0.631 | 0 | — |
| s8-055 | OpenPath Clip O2 | fixture-019 | fixture-019, fixture-020, fixture-008, fixture-009, fixture-024, fixture-013, fixture-018, fixture-023, fixture-012, fixture-022 | 1.000 | 1.000 | 0 | — |
| s8-056 | OpenPath OpenPath Clip O2 | fixture-019 | fixture-019, fixture-020, fixture-008, fixture-009, fixture-013, fixture-024, fixture-018, fixture-007, fixture-012, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-057 | OpenPath Clip O2 价格 299.00 CNY | fixture-019 | fixture-019, fixture-020, fixture-009, fixture-008, fixture-018, fixture-005, fixture-012, fixture-013, fixture-023, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-058 | OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-022, fixture-023, fixture-012, fixture-014, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-059 | OpenPath OpenPath Clip O5 | fixture-020 | fixture-020, fixture-019, fixture-008, fixture-009, fixture-013, fixture-012, fixture-007, fixture-022, fixture-023, fixture-024 | 1.000 | 1.000 | 0 | — |
| s8-060 | OpenPath Clip O5 价格 549.00 CNY | fixture-020 | fixture-020, fixture-019, fixture-009, fixture-008, fixture-013, fixture-012, fixture-005, fixture-018, fixture-023, fixture-015 | 1.000 | 1.000 | 0 | — |
| s8-061 | BoneWave City B3 | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-016, fixture-017, fixture-012, fixture-003, fixture-004, fixture-013, fixture-007 | 1.000 | 1.000 | 0 | — |
| s8-062 | BoneWave BoneWave City B3 | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-016, fixture-017, fixture-003, fixture-004, fixture-012, fixture-007, fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-063 | BoneWave City B3 价格 469.00 CNY | fixture-021 | fixture-021, fixture-011, fixture-010, fixture-012, fixture-005, fixture-013, fixture-018, fixture-004, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-064 | ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-065 | ClearCall ClearCall Bud C8 | fixture-022 | fixture-022, fixture-023, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-016, fixture-017, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-066 | ClearCall Bud C8 价格 429.00 CNY | fixture-022 | fixture-012, fixture-013, fixture-022, fixture-023, fixture-018, fixture-005, fixture-024, fixture-017, fixture-011, fixture-019 | 1.000 | 0.500 | 0 | — |
| s8-067 | ClearCall Air C5 | fixture-023 | fixture-023, fixture-022, fixture-012, fixture-013, fixture-018, fixture-004, fixture-024, fixture-017, fixture-014, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-068 | ClearCall ClearCall Air C5 | fixture-023 | fixture-023, fixture-022, fixture-012, fixture-013, fixture-018, fixture-024, fixture-005, fixture-017, fixture-014, fixture-016 | 1.000 | 1.000 | 0 | — |
| s8-069 | ClearCall Air C5 价格 279.00 CNY | fixture-023 | fixture-023, fixture-012, fixture-013, fixture-018, fixture-005, fixture-022, fixture-004, fixture-017, fixture-014, fixture-019 | 1.000 | 1.000 | 0 | — |
| s8-070 | Auralis Studio Wired 80 | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-002, fixture-015, fixture-001, fixture-022, fixture-008 | 1.000 | 1.000 | 0 | — |
| s8-071 | Auralis Auralis Studio Wired 80 | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-015, fixture-002, fixture-001, fixture-022, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-072 | Auralis Studio Wired 80 价格 1599.00 CNY | fixture-024 | fixture-024, fixture-017, fixture-016, fixture-018, fixture-014, fixture-015, fixture-002, fixture-001, fixture-005, fixture-013 | 1.000 | 1.000 | 0 | — |
| s8-073 | Auralis Metro ANC 40 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-074 | Auralis Studio ANC 55 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-075 | MetroTone Buds N8 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-076 | MetroTone Air S2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-077 | QuietArc Q1 Lite | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-078 | QuietArc Q3 Travel | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-079 | QuietArc Q5 Office | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-080 | OpenPath Loop 10 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-081 | OpenPath Loop 14 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-082 | BoneWave Run B1 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-083 | BoneWave Swim B2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-084 | ClearCall Work C20 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-085 | ClearCall Work C40 ANC | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-086 | Auralis Pocket P2 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-087 | Auralis Pocket P4 ANC | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-088 | MetroTone Cable M1 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-089 | MetroTone Cable M3 | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-090 | QuietArc Q7 Reference | ∅ | ∅ | n/a | n/a | 0 | — |
| s8-091 | 通勤地铁主动降噪，预算七百元 | fixture-003, fixture-006 | fixture-021, fixture-001, fixture-002, fixture-006, fixture-013, fixture-015, fixture-018, fixture-016, fixture-017, fixture-005 | 0.500 | 0.264 | 0 | — |
| s8-092 | 开放式跑步耳机，防水至少 IP55 | fixture-009 | fixture-010, fixture-008, fixture-019, fixture-009, fixture-020, fixture-011, fixture-014, fixture-004, fixture-023, fixture-015 | 1.000 | 0.431 | 0 | — |
| s8-093 | 游泳训练骨传导 IP68 | fixture-011 | fixture-011, fixture-010, fixture-021, fixture-022, fixture-014, fixture-004, fixture-009, fixture-019, fixture-008, fixture-023 | 1.000 | 1.000 | 0 | — |
| s8-094 | 办公室开会要杆式麦克风 | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013, fixture-022, fixture-005, fixture-020, fixture-023, fixture-015, fixture-001, fixture-006 | 1.000 | 1.000 | 0 | — |
| s8-095 | 百元以内有线入耳通话 | fixture-016 | fixture-016, fixture-017, fixture-024, fixture-022, fixture-023, fixture-015, fixture-007, fixture-014, fixture-004, fixture-005 | 1.000 | 1.000 | 0 | — |
| s8-096 | 长续航折叠旅行降噪头戴 | fixture-006 | fixture-006, fixture-002, fixture-009, fixture-005, fixture-001, fixture-013, fixture-015, fixture-016, fixture-014, fixture-004 | 1.000 | 1.000 | 0 | — |
| s8-097 | 戴眼镜也舒适的通勤头戴耳机 | fixture-001 | fixture-001, fixture-006, fixture-021, fixture-018, fixture-024, fixture-005, fixture-002, fixture-015, fixture-016, fixture-017 | 1.000 | 1.000 | 0 | — |
| s8-098 | 不要堵耳的轻量耳夹 | fixture-019, fixture-020 | fixture-008, fixture-019, fixture-004, fixture-014, fixture-012, fixture-009, fixture-020, fixture-003, fixture-017, fixture-022 | 1.000 | 0.591 | 0 | — |
| s8-099 | 高阻抗有线头戴室内听音 | fixture-024 | fixture-024, fixture-016, fixture-017, fixture-018, fixture-005, fixture-001, fixture-002, fixture-006, fixture-007, fixture-012 | 1.000 | 1.000 | 0 | — |
| s8-100 | 五百元内小巧入耳主动降噪 | fixture-003 | fixture-015, fixture-002, fixture-016, fixture-017, fixture-013, fixture-014, fixture-004, fixture-018, fixture-023, fixture-001 | 0.000 | 0.000 | 0 | — |
| s8-101 | 抗风噪户外通话无线耳机 | fixture-006, fixture-009 | fixture-010, fixture-022, fixture-005, fixture-020, fixture-007, fixture-023, fixture-015, fixture-001, fixture-014, fixture-009 | 0.500 | 0.177 | 0 | — |
| s8-102 | 半入耳无线通话，三百元内 | fixture-004, fixture-023 | fixture-023, fixture-022, fixture-004, fixture-015, fixture-017, fixture-014, fixture-005, fixture-020, fixture-007, fixture-003 | 1.000 | 0.920 | 0 | — |
