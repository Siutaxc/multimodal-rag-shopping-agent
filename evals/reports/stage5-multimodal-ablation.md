# Stage 5 multimodal retrieval ablation

- Dataset: `shoplens-stage5-multimodal-fixture` / `2026-07-22.1`
- Corpus: 24 synthetic CC0 fixtures
- Queries: 12 pure image + 12 multimodal
- Models: `{'image_embedding': 'google/siglip2-base-patch16-224@fixture-visual-v1:768'}`
- Parameters: `{'image_candidate_k': 50, 'fusion_candidate_k': 30, 'rrf_k': 60, 'text_weight': 1.0, 'image_weight': 1.25}`

| Mode | Queries | R@5 | R@10 | P@5 | nDCG@10 | MRR | Hard violations | Empty accuracy | P50 ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pure_image | 12 | 1.0000 | 1.0000 | 0.7091 | 0.9809 | 1.0000 | 0.0000 | 1.0000 | 48.177 | 78.473 |
| mixed_image_only | 12 | 1.0000 | 1.0000 | 0.2909 | 0.9090 | 0.8939 | 0.0000 | 1.0000 | 52.235 | 56.290 |
| mixed_text_only | 12 | 1.0000 | 1.0000 | 0.2909 | 0.9755 | 1.0000 | 0.0000 | 1.0000 | 71.683 | 88.177 |
| mixed_full | 12 | 1.0000 | 1.0000 | 0.2909 | 0.9037 | 0.8939 | 0.0000 | 1.0000 | 61.337 | 65.517 |

## Failure analysis

- **pure_image**: img-01, img-02, img-06, img-08, img-09, img-10, img-11
- **mixed_image_only**: mix-03, mix-08, mix-10
- **mixed_text_only**: mix-10
- **mixed_full**: mix-03, mix-08, mix-10

## Limitations

- The corpus contains only 24 synthetic CC0 products and synthetic artwork.
- The deterministic pixel provider validates engineering behavior, not SigLIP2 quality.
- Reference images are checked-in product artwork; open-domain photos are not measured.
- All annotated failures are retained and cannot be generalized to production traffic.

## Complete query trace

### pure_image

| ID | Reference | Text | Expected | Retrieved | R@10 | nDCG@10 | Violations |
|---|---|---|---|---|---:|---:|---:|
| img-01 | fixture-001 | — | fixture-001, fixture-002, fixture-006, fixture-018 | fixture-001, fixture-018, fixture-002, fixture-024, fixture-006, fixture-005 | 1.000 | 0.946 | 0 |
| img-02 | fixture-003 | — | fixture-003, fixture-015, fixture-016, fixture-022 | fixture-003, fixture-015, fixture-022, fixture-016, fixture-014 | 1.000 | 0.973 | 0 |
| img-03 | fixture-004 | — | fixture-004, fixture-017, fixture-023 | fixture-004, fixture-023, fixture-017 | 1.000 | 1.000 | 0 |
| img-04 | fixture-007 | — | fixture-007, fixture-012, fixture-013 | fixture-007, fixture-012, fixture-013 | 1.000 | 1.000 | 0 |
| img-05 | fixture-008 | — | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-008, fixture-019, fixture-020, fixture-009 | 1.000 | 1.000 | 0 |
| img-06 | fixture-010 | — | fixture-010, fixture-011, fixture-021 | fixture-010, fixture-011, fixture-021 | 1.000 | 0.972 | 0 |
| img-07 | fixture-014 | — | fixture-003, fixture-014, fixture-015, fixture-022 | fixture-014, fixture-022, fixture-003, fixture-015, fixture-016 | 1.000 | 1.000 | 0 |
| img-08 | fixture-018 | — | fixture-001, fixture-002, fixture-006, fixture-018 | fixture-018, fixture-001, fixture-002, fixture-024, fixture-006, fixture-005 | 1.000 | 0.996 | 0 |
| img-09 | fixture-020 | — | fixture-008, fixture-009, fixture-019, fixture-020 | fixture-020, fixture-008, fixture-019, fixture-009 | 1.000 | 0.959 | 0 |
| img-10 | fixture-021 | — | fixture-010, fixture-011, fixture-021 | fixture-021, fixture-011, fixture-010 | 1.000 | 0.972 | 0 |
| img-11 | fixture-023 | — | fixture-004, fixture-017, fixture-023 | fixture-023, fixture-017, fixture-004 | 1.000 | 0.972 | 0 |
| img-12 | fixture-024 | — | ∅ | ∅ | n/a | n/a | 0 |

### mixed_image_only

| ID | Reference | Text | Expected | Retrieved | R@10 | nDCG@10 | Violations |
|---|---|---|---|---|---:|---:|---:|
| mix-01 | fixture-002 | 地铁通勤降噪 戴眼镜舒适 | fixture-001, fixture-006 | fixture-001, fixture-006 | 1.000 | 1.000 | 0 |
| mix-02 | fixture-001 | 室内参考声音 有线 | fixture-018 | fixture-018 | 1.000 | 1.000 | 0 |
| mix-03 | fixture-003 | 通话麦克风清晰 | fixture-003, fixture-022 | fixture-003, fixture-022 | 1.000 | 0.834 | 0 |
| mix-04 | fixture-004 | 白色有线 线控麦克风 | fixture-017 | fixture-017 | 1.000 | 1.000 | 0 |
| mix-05 | fixture-007 | 办公室会议 杆式麦克风 | fixture-007, fixture-012 | fixture-007, fixture-012 | 1.000 | 1.000 | 0 |
| mix-06 | fixture-008 | 户外运动 防水 开放不堵耳 | fixture-008, fixture-019 | fixture-008, fixture-019 | 1.000 | 1.000 | 0 |
| mix-07 | fixture-011 | 游泳训练 高防水 | fixture-011 | fixture-011, fixture-021, fixture-010 | 1.000 | 1.000 | 0 |
| mix-08 | fixture-014 | 便携 主动降噪 | fixture-015 | fixture-022, fixture-003, fixture-015 | 1.000 | 0.500 | 0 |
| mix-09 | fixture-018 | 高阻抗有线 室内使用 | fixture-024 | fixture-024 | 1.000 | 1.000 | 0 |
| mix-10 | fixture-019 | 长续航 开放式 | fixture-009, fixture-020 | fixture-008, fixture-020, fixture-009 | 1.000 | 0.665 | 0 |
| mix-11 | fixture-021 | 城市通勤 骨传导 | fixture-021 | fixture-021, fixture-010 | 1.000 | 1.000 | 0 |
| mix-12 | fixture-001 | 主动降噪头戴式 | ∅ | ∅ | n/a | n/a | 0 |

### mixed_text_only

| ID | Reference | Text | Expected | Retrieved | R@10 | nDCG@10 | Violations |
|---|---|---|---|---|---:|---:|---:|
| mix-01 | fixture-002 | 地铁通勤降噪 戴眼镜舒适 | fixture-001, fixture-006 | fixture-001, fixture-006 | 1.000 | 1.000 | 0 |
| mix-02 | fixture-001 | 室内参考声音 有线 | fixture-018 | fixture-018 | 1.000 | 1.000 | 0 |
| mix-03 | fixture-003 | 通话麦克风清晰 | fixture-003, fixture-022 | fixture-022, fixture-003 | 1.000 | 1.000 | 0 |
| mix-04 | fixture-004 | 白色有线 线控麦克风 | fixture-017 | fixture-017 | 1.000 | 1.000 | 0 |
| mix-05 | fixture-007 | 办公室会议 杆式麦克风 | fixture-007, fixture-012 | fixture-007, fixture-012 | 1.000 | 1.000 | 0 |
| mix-06 | fixture-008 | 户外运动 防水 开放不堵耳 | fixture-008, fixture-019 | fixture-008, fixture-019 | 1.000 | 1.000 | 0 |
| mix-07 | fixture-011 | 游泳训练 高防水 | fixture-011 | fixture-011, fixture-010, fixture-021 | 1.000 | 1.000 | 0 |
| mix-08 | fixture-014 | 便携 主动降噪 | fixture-015 | fixture-015, fixture-003, fixture-022 | 1.000 | 1.000 | 0 |
| mix-09 | fixture-018 | 高阻抗有线 室内使用 | fixture-024 | fixture-024 | 1.000 | 1.000 | 0 |
| mix-10 | fixture-019 | 长续航 开放式 | fixture-009, fixture-020 | fixture-009, fixture-008, fixture-020 | 1.000 | 0.731 | 0 |
| mix-11 | fixture-021 | 城市通勤 骨传导 | fixture-021 | fixture-021, fixture-010 | 1.000 | 1.000 | 0 |
| mix-12 | fixture-001 | 主动降噪头戴式 | ∅ | ∅ | n/a | n/a | 0 |

### mixed_full

| ID | Reference | Text | Expected | Retrieved | R@10 | nDCG@10 | Violations |
|---|---|---|---|---|---:|---:|---:|
| mix-01 | fixture-002 | 地铁通勤降噪 戴眼镜舒适 | fixture-001, fixture-006 | fixture-001, fixture-006 | 1.000 | 1.000 | 0 |
| mix-02 | fixture-001 | 室内参考声音 有线 | fixture-018 | fixture-018 | 1.000 | 1.000 | 0 |
| mix-03 | fixture-003 | 通话麦克风清晰 | fixture-003, fixture-022 | fixture-003, fixture-022 | 1.000 | 0.834 | 0 |
| mix-04 | fixture-004 | 白色有线 线控麦克风 | fixture-017 | fixture-017 | 1.000 | 1.000 | 0 |
| mix-05 | fixture-007 | 办公室会议 杆式麦克风 | fixture-007, fixture-012 | fixture-007, fixture-012 | 1.000 | 1.000 | 0 |
| mix-06 | fixture-008 | 户外运动 防水 开放不堵耳 | fixture-008, fixture-019 | fixture-008, fixture-019 | 1.000 | 1.000 | 0 |
| mix-07 | fixture-011 | 游泳训练 高防水 | fixture-011 | fixture-011, fixture-021, fixture-010 | 1.000 | 1.000 | 0 |
| mix-08 | fixture-014 | 便携 主动降噪 | fixture-015 | fixture-022, fixture-003, fixture-015 | 1.000 | 0.500 | 0 |
| mix-09 | fixture-018 | 高阻抗有线 室内使用 | fixture-024 | fixture-024 | 1.000 | 1.000 | 0 |
| mix-10 | fixture-019 | 长续航 开放式 | fixture-009, fixture-020 | fixture-008, fixture-009, fixture-020 | 1.000 | 0.606 | 0 |
| mix-11 | fixture-021 | 城市通勤 骨传导 | fixture-021 | fixture-021, fixture-010 | 1.000 | 1.000 | 0 |
| mix-12 | fixture-001 | 主动降噪头戴式 | ∅ | ∅ | n/a | n/a | 0 |
