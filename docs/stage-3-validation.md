# 阶段 3 验收记录

日期：2026-07-22  
工作区：`D:\CodexProjects\bytedance`

## 自动化检查

| 检查 | 结果 |
|---|---|
| Ruff | 通过 |
| mypy strict | 通过 |
| 后端单元测试 | 32 通过，2 个集成测试按标记排除 |
| PostgreSQL 集成测试 | 2 通过 |
| ESLint | 通过，0 warning |
| TypeScript strict | 通过 |
| Vitest | 3 通过 |
| Next.js 生产构建 | 通过 |
| `npm run check` | 完整通过 |

集成测试在专用临时数据库中执行完整 `0001 → 0002` 迁移和 `alembic check`，导入 24 件 Fixture，验证重复导入、`tsvector`、精确型号、硬过滤、30 条基线计算及真实 FastAPI HTTP 路由；结束后删除临时数据库。

## 真实主库与 Compose

- 主库从阶段 2 的 `20260722_0001` 原位升级到 `20260722_0002`；商品数保持 24。
- 24 个商品文档均完成 `search_text/search_vector` 回填，GIN 索引可用。
- 既有两次摄取记录保持不变：首次 24 成功，第二次 24 跳过。
- API 与 Web 镜像完成生产构建；Web、API、PostgreSQL、Redis 四个容器均为 `healthy`。
- 所有验收请求使用 HTTP，未使用 WebSocket。

## 词法基线

语料：24 件 CC0 人工 Fixture。查询：30 条，其中 29 条有相关商品标注、1 条预期空结果。

| 指标 | 实测值 |
|---|---:|
| Recall@5 | 0.9844 |
| Recall@10 | 1.0000 |
| Precision@5 | 0.4552 |
| nDCG@10 | 1.0000 |
| MRR | 1.0000 |
| 硬条件违反率 | 0.0000 |
| 空结果准确率 | 1.0000 |

这些结果只证明当前确定性小样本上的工程正确性。查询集是为 24 件 Fixture 编写的回归集，不能外推为真实商品库或开放域中文检索效果。完整逐查询证据见 `evals/reports/stage3-lexical-baseline.md` 与 JSON 报告。

## 蓝图验收对照

| 验收项 | 状态 | 证据 |
|---|---|---|
| 品牌、型号和关键参数准确搜索 | 通过 | 12 条精确型号查询、中文参数/品类查询与 PostgreSQL 集成测试 |
| 所有结构化过滤通过 | 通过 | API Schema、仓储参数化过滤、硬条件违反率 0 |
| 第一份可复现词法基线报告 | 通过 | 30 条固定 `source_id` 标注，Markdown/JSON 双产物 |
| 前端“搜索 → 查看详情” | 通过 | Vitest 交互测试、Next.js 生产构建与真实 HTTP 烟测 |

## 已知限制与延期项

- 当前只有 24 件人工 Fixture，外部 200 条样本仍因许可未明确而延期，没有下载或冒充完成。
- `simple` FTS 不能做通用中文分词；阶段 3 只加入可审查的事实别名和原文场景词。
- 当前未实现 Embedding、向量召回、HNSW、RRF、Reranker、LLM 条件解析或 Agent；这些属于阶段 4 及以后。
- 工作区根目录的无效 `.git` 目录保持原样，没有初始化或删除。
