# 阶段 2 验收记录

日期：2026-07-22  
工作区：`D:\CodexProjects\bytedance`

## 自动化检查

| 检查 | 结果 |
|---|---|
| Ruff | 通过 |
| mypy strict | 31 个源码/测试文件通过 |
| 后端单元测试 | 25 通过，2 个集成测试按标记排除 |
| PostgreSQL 集成测试 | 2 通过 |
| ESLint | 通过，0 warning |
| TypeScript strict | 通过 |
| Vitest | 1 通过 |
| Next.js 生产构建 | 通过 |
| `npm run check` | 完整通过 |

集成测试在独立的 `shoplens_stage2_test_<uuid>` 空数据库中执行首个 Alembic 迁移，并运行 `alembic check` 确认 ORM 与迁移无漂移；测试结束后删除该临时数据库。

## 真实 Compose 验收

- API/Web 镜像重建成功，API 容器启动时将主库升级至 `20260722_0001`。
- Web、API、PostgreSQL、Redis 均成功启动，API 通过健康检查。
- 主库首次 Fixture 导入：总计 24，成功 24，失败 0，跳过 0。
- 主库第二次相同导入：总计 24，成功 0，失败 0，跳过 24。
- 主库最终商品数：24；摄取任务数：2。
- `/api/v1/health/ready` 返回 `ready`，PostgreSQL、pgvector、Redis 均为 `ok`。
- 真实过滤请求 `category=in_ear&price_max=500&currency=CNY&anc=true&battery_hours_min=7&codec=AAC` 返回 2 件商品，硬条件违规数为 0。
- 商品详情包含来源名称、HTTPS 来源 URL 和 UTC 价格观测时间。

## 蓝图验收对照

| 验收项 | 状态 | 证据 |
|---|---|---|
| 重复导入不产生重复商品 | 通过 | 第二次导入 24 条全部跳过，商品数保持 24 |
| 非法价格、单位和枚举有明确错误 | 通过 | 单元测试和集成任务覆盖负价格、超精度价格、未知单位、未知类别与未知布尔值 |
| 商品详情包含来源与价格时间戳 | 通过 | 真实 HTTP 详情烟测 |
| 过滤结果不存在硬条件违规 | 通过 | PostgreSQL 仓储测试与真实 HTTP 烟测均为 0 违规 |
| 数据库迁移可从空库完整执行 | 通过 | 临时空库 `upgrade head`，随后 `alembic check` 无漂移 |
| 摄取任务有成功、失败和跳过统计 | 通过 | 成功/失败/跳过任务测试及主库两次导入记录 |
| 建立 20～50 件 Fixture | 通过 | 24 件 CC0 人工样本 |
| 导入首批 200 件外部样本 | 待办 | 上游数据许可未明确、全量规模过大、部分原始链接失效，未下载 |

## 结论

阶段 2 的代码、Fixture 模式和蓝图六项验收标准均已闭环；外部 200 条样本仍是已知延期项。用户已明确要求继续阶段 3，因此词法基线先使用现有 24 件确定性 Fixture，并在评测报告中标注规模限制。许可与小样本 HTTPS 来源明确前，仍不得下载 Electronics 全量数据或图片，也不得声称外部 200 条样本已完成。
