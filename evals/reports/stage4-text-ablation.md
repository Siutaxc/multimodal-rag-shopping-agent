# Stage 4 text retrieval ablation

- Dataset: `shoplens-stage4-text-ablation` / `2026-07-22.1`
- Corpus: 24 synthetic CC0 fixtures
- Queries: 48 (30 frozen lexical + 18 semantic)
- Generated: `2026-07-22T03:37:18.733341+00:00`
- Models: `{'embedding': 'BAAI/bge-m3@fixture-semantic-v1:1024', 'reranker': 'BAAI/bge-reranker-v2-m3@fixture-semantic-v1'}`
- Parameters: `{'lexical_candidate_k': 50, 'dense_candidate_k': 50, 'fusion_candidate_k': 30, 'rerank_top_k': 30, 'rrf_k': 60}`

| Mode | R@5 | R@10 | P@5 | nDCG@10 | MRR | Hard violations | Empty accuracy | P50 ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.6206 | 0.6304 | 0.2870 | 0.6304 | 0.6304 | 0.0000 | 1.0000 | 3.785 | 8.900 |
| dense | 0.9233 | 0.9791 | 0.4087 | 0.9239 | 0.9227 | 0.0000 | 1.0000 | 6.360 | 10.891 |
| rrf | 0.9394 | 0.9928 | 0.4261 | 0.9648 | 0.9589 | 0.0000 | 1.0000 | 8.730 | 10.996 |
| rerank | 0.9233 | 0.9791 | 0.4087 | 0.9239 | 0.9227 | 0.0000 | 1.0000 | 19.564 | 28.258 |

## Failure analysis

- **lexical**: sem-01, sem-02, sem-03, sem-04, sem-05, sem-06, sem-07, sem-08, sem-09, sem-10, sem-11, sem-12, sem-13, sem-14, sem-15, sem-16, sem-18
- **dense**: lex-01, lex-08, lex-10, lex-16, lex-21, lex-22, sem-01, sem-03, sem-04, sem-06, sem-08, sem-10, sem-18
- **rrf**: sem-01, sem-03, sem-04, sem-06, sem-08, sem-10, sem-18
- **rerank**: lex-01, lex-08, lex-10, lex-16, lex-21, lex-22, sem-01, sem-03, sem-04, sem-06, sem-08, sem-10, sem-18

## Limitations

- The corpus contains only 24 synthetic CC0 fixture products.
- The deterministic offline providers validate retrieval plumbing, not BGE production quality.
- All failures are retained; metrics must not be generalized to open-domain shopping search.

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
