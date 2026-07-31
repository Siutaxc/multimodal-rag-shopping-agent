# 评测、性能与数字溯源

## 复现命令

先运行 `npm run stack:fixture`。下面每条命令都从版本化数据集生成 Markdown 和 JSON；报告目录是 `evals/reports/`。

~~~powershell
npm run eval:lexical       # 阶段 3：30 条冻结词法基线
npm run eval:text          # 阶段 4：30+18 条文本消融
npm run eval:multimodal    # 阶段 5：12 纯图 + 12 图文
npm run eval:agent         # 阶段 6：15 个多轮 Agent 场景
npm run eval:stage8        # 阶段 8：150 条扩展文本消融
npm run perf:stage8        # 5k/50k 合成规模与索引前后执行计划
npm run verify:fixture     # 阶段 9：完整 HTTP 交付烟测
~~~

`perf:stage8` 会创建明确命名的 UNLOGGED 临时基准表，并在 `finally` 删除；不会修改规范商品表。报告包含环境、数据量、20 次采样的 P50/P95、索引构建时间和完整 `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`。

## 文本检索结果

阶段 8 在相同 24 件 Fixture 上运行 150 条查询。所有失败 ID 均保存在 JSON/Markdown；RRF 是当前确定性 Fixture 的最佳组，重排没有超过 RRF，这是保留的负结果。

| 模式 | Recall@5 | Recall@10 | Precision@5 | nDCG@10 | MRR | 硬条件违反率 |
|---|---:|---:|---:|---:|---:|---:|
| 词法 | 0.5888 | 0.5923 | 0.1754 | 0.5923 | 0.5923 | 0.0000 |
| 稠密 | 0.9498 | 0.9772 | 0.2754 | 0.9072 | 0.8914 | 0.0000 |
| RRF | **0.9555** | **0.9821** | **0.2815** | **0.9464** | **0.9375** | 0.0000 |
| 重排 | 0.9498 | 0.9772 | 0.2754 | 0.9072 | 0.8914 | 0.0000 |

证据：`evals/reports/stage8-text-ablation.json` 与 `.md`。阶段 3 的 30 条小样本词法基线 Recall@10/nDCG@10 都是 1.0000，但只说明冻结工程回归正确，不能作为开放域质量主张。

## 多模态与 Agent

阶段 5 的 24 条多模态查询中，完整融合 nDCG@10 为 0.9037，低于图文查询的文字消融 0.9755；图片权重未在真实图片分布上校准。阶段 6 的 15 个场景中，任务完成率、工具选择正确率、引用精度和引用覆盖率均为 1.0000，384 条结构化事实声明的幻觉率为 0.0000，最大工具调用 3；这些数字来自确定性 Agent Fixture，不代表真实 LLM 能力。

证据：`evals/reports/stage5-multimodal-ablation.json`、`evals/reports/stage6-agent-evidence.json`。

## 50k 索引前后 P95

测试环境：Windows 11、12 逻辑 CPU、Python 3.13.7、PostgreSQL 16.14、pgvector 0.8.5；50,000 行来自重复并扰动 24 件 Fixture 的明确合成数据。

| 操作 | 索引前 P95 (ms) | 索引后 P95 (ms) | 主要执行路径 |
|---|---:|---:|---|
| 结构化硬过滤 | 23.389 | **0.462** | covering index / index-only scan |
| PostgreSQL FTS | 39.634 | **10.681** | GIN bitmap scan + Top-N |
| pgvector ANN | 239.207 | **1.113** | HNSW index scan |

50k 造数 18.151 秒，索引构建 17.748 秒。结果只描述该硬件、该合成分布和 20 次暖机采样，不能外推生产 SLO。

## 简历数字溯源表

| 可使用的数字 | 准确表述 | 证据 |
|---|---|---|
| 24 件商品 | 24 件 CC0 人工 Fixture | `data/fixtures/headphones.json`、阶段 9 烟测 JSON |
| 150 条查询 | 30 条冻结词法 + 18 条语义 + 102 条扩展回归 | `stage8_text_queries.json` 与阶段 8 报告 |
| RRF Recall@10 0.9821 / nDCG@10 0.9464 | 仅确定性 Fixture | 阶段 8 文本消融 JSON |
| 15 个 Agent 场景 / 384 条事实 | Fixture 下 0 结构化事实幻觉 | 阶段 6 Agent JSON |
| 最多 4 步 | 代码硬上限 4；评测实测最大 3 | `agent_max_tool_steps`、阶段 6 JSON |
| 50k P95 0.462/10.681/1.113 ms | 指索引后 DB 查询，不是端到端 API | 阶段 8 性能 JSON |
| 183 个后端单元测试、9 个前端测试、10+2 个 E2E | 指阶段 9 本机验收批次 | `docs/stage-9-validation.md`，不要当作产品质量指标 |

## 解释规则

任何对外材料都必须同时说明数据范围与 Provider 类型。禁止把 Fixture 报告称为 BGE-M3、SigLIP2 或真实 LLM 的质量；禁止把数据库查询 P95 称为端到端延迟；禁止删除失败查询或改写冻结标注来制造提升。真实 Provider 接入后应新建版本和独立报告，而不是覆盖当前基线。
