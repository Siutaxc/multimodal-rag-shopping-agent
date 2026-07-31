# Stage 3 lexical baseline

- Dataset: `shoplens-stage3-lexical` / `2026-07-22.1`
- Search document: `stage3-lexical-v1`
- Corpus: 24 synthetic CC0 fixture products
- Generated: `2026-07-22T03:37:14.740839+00:00`
- Queries: 30 (29 judged, 1 empty-result)
- Recall@5: 0.9844
- Recall@10: 1.0000
- Precision@5: 0.4552
- nDCG@10: 1.0000
- MRR: 1.0000
- Hard-condition violation rate: 0.0000
- Empty-result accuracy: 1.0000

## Limitations

- The corpus contains only 24 synthetic CC0 fixtures.
- Queries were authored for deterministic engineering regression, not production quality claims.
- PostgreSQL simple FTS has no general Chinese word segmentation; documents expose explicit fact aliases and observed scene terms.

## Query trace

| ID | Query | Expected | Retrieved | R@10 | nDCG@10 | Violations |
|---|---|---|---|---:|---:|---:|
| lex-01 | Auralis Metro ANC 40 | fixture-001 | fixture-001 | 1.000 | 1.000 | 0 |
| lex-02 | Auralis Studio ANC 55 | fixture-002 | fixture-002 | 1.000 | 1.000 | 0 |
| lex-03 | MetroTone Buds N8 | fixture-003 | fixture-003 | 1.000 | 1.000 | 0 |
| lex-04 | QuietArc Q3 Travel | fixture-006 | fixture-006 | 1.000 | 1.000 | 0 |
| lex-05 | OpenPath Loop 14 | fixture-009 | fixture-009 | 1.000 | 1.000 | 0 |
| lex-06 | BoneWave Swim B2 | fixture-011 | fixture-011 | 1.000 | 1.000 | 0 |
| lex-07 | ClearCall Work C40 ANC | fixture-013 | fixture-013 | 1.000 | 1.000 | 0 |
| lex-08 | Auralis Pocket P4 ANC | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 |
| lex-09 | MetroTone Cable M1 | fixture-016 | fixture-016 | 1.000 | 1.000 | 0 |
| lex-10 | QuietArc Q7 Reference | fixture-018 | fixture-018 | 1.000 | 1.000 | 0 |
| lex-11 | OpenPath Clip O5 | fixture-020 | fixture-020 | 1.000 | 1.000 | 0 |
| lex-12 | ClearCall Bud C8 | fixture-022 | fixture-022 | 1.000 | 1.000 | 0 |
| lex-13 | Auralis | fixture-001, fixture-002, fixture-014, fixture-015, fixture-024 | fixture-001, fixture-014, fixture-015, fixture-002, fixture-024 | 1.000 | 1.000 | 0 |
| lex-14 | QuietArc | fixture-005, fixture-006, fixture-007, fixture-018 | fixture-005, fixture-006, fixture-007, fixture-018 | 1.000 | 1.000 | 0 |
| lex-15 | BoneWave | fixture-010, fixture-011, fixture-021 | fixture-021, fixture-010, fixture-011 | 1.000 | 1.000 | 0 |
| lex-16 | 主动降噪 | fixture-001, fixture-002, fixture-003, fixture-006, fixture-013, fixture-015, fixture-022 | fixture-001, fixture-015, fixture-002, fixture-022, fixture-013, fixture-003, fixture-006 | 1.000 | 1.000 | 0 |
| lex-17 | 骨传导 | fixture-010, fixture-011, fixture-021 | fixture-021, fixture-010, fixture-011 | 1.000 | 1.000 | 0 |
| lex-18 | 开放式 | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-019, fixture-020, fixture-008, fixture-009 | 1.000 | 1.000 | 0 |
| lex-19 | 半入耳式 | fixture-004, fixture-017, fixture-023 | fixture-023, fixture-004, fixture-017 | 1.000 | 1.000 | 0 |
| lex-20 | 有线 | fixture-016, fixture-017, fixture-018, fixture-024 | fixture-024, fixture-016, fixture-017, fixture-018 | 1.000 | 1.000 | 0 |
| lex-21 | 通话 入耳式 | fixture-003, fixture-014, fixture-015, fixture-016, fixture-022 | fixture-016, fixture-014, fixture-022, fixture-003, fixture-015 | 1.000 | 1.000 | 0 |
| lex-22 | 通勤 | fixture-001, fixture-021 | fixture-001, fixture-021 | 1.000 | 1.000 | 0 |
| lex-23 | 办公 | fixture-007, fixture-012, fixture-013 | fixture-012, fixture-013, fixture-007 | 1.000 | 1.000 | 0 |
| lex-24 | 户外 运动 | fixture-010 | fixture-010 | 1.000 | 1.000 | 0 |
| lex-25 | headphones | fixture-004, fixture-014, fixture-016, fixture-017, fixture-019, fixture-023 | fixture-014, fixture-023, fixture-004, fixture-016, fixture-017, fixture-019 | 1.000 | 1.000 | 0 |
| lex-26 | wireless | fixture-001, fixture-006 | fixture-001, fixture-006 | 1.000 | 1.000 | 0 |
| lex-27 | wireless | fixture-015 | fixture-015 | 1.000 | 1.000 | 0 |
| lex-28 | microphone | fixture-012, fixture-013, fixture-022 | fixture-022, fixture-012, fixture-013 | 1.000 | 1.000 | 0 |
| lex-29 | headphones | fixture-014 | fixture-014 | 1.000 | 1.000 | 0 |
| lex-30 | headphones | ∅ | ∅ | n/a | n/a | 0 |
