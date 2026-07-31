# 阶段 6 验收记录

验收日期：2026-07-22  
工作区：`D:\CodexProjects\bytedance`

## 验收结论

阶段 6 已完成并通过静态检查、单元测试、临时 PostgreSQL/pgvector + Redis 集成、离线 Agent/证据评测、Compose 重建和真实 HTTP/UI 验收。阶段 3～5 的数据集、Provider 和报告未改写。

## 静态检查与测试

- Ruff：通过。
- mypy strict：通过，应用与测试共 87 个 Python 源文件无类型错误。
- API 单元测试：173 通过，2 个集成测试按标记排除。
- 其中包含 100 条逐价格事实精确性用例。
- ESLint：通过，零 warning。
- TypeScript strict：通过。
- Vitest：5 通过。
- Next.js 生产构建：通过。
- PostgreSQL/pgvector + Redis 集成：2 通过。

新增覆盖包括白名单 Schema、价格/续航歧义、会话继承/覆盖/清除/隔离、最多工具步数、显式对比、跨商品错误引用、商品描述/评论提示注入、HTTP Provider Schema、WebSocket 拒绝、解析超时、回答超时、Redis 会话/轨迹和真实 Agent HTTP。

## Agent/证据评测

语料：24 件合成 CC0 商品；15 个多轮 Agent 场景。

| 指标 | 实测值 |
|---|---:|
| 任务完成率 | 1.0000 |
| 工具选择正确率 | 1.0000 |
| 引用精确率 | 1.0000 |
| 引用覆盖率 | 1.0000 |
| 结构化事实条数 | 384 |
| 结构化事实幻觉率 | 0.0000 |
| 条件继承/覆盖/清除正确率 | 1.0000 |
| 平均工具调用数 | 2.200 |
| 最大工具调用数 | 3 |
| 无效循环率 | 0.0000 |
| 完整回答 P50 | 26.303 ms |
| 完整回答 P95 | 138.085 ms |

首轮评测发现“续航至少 7 小时”被通用“至少”规则误识别为最低价格，条件正确率为 0.8667。价格正则随后收紧为必须出现价格上下文或货币单位，增加回归测试后重新评测为 1.0000；没有修改失败查询或期望结果。

上述数字来自确定性 Fixture Provider 和 24 件人工商品，只证明工程回归，不能外推为真实 LLM 或生产导购效果。

## Compose 与真实 HTTP

API 与 Web 镜像均重建成功。容器依赖下载期间连续出现 `IncompleteRead` / `ECONNRESET`；API Dockerfile 增加有界 pip 重试，Web Dockerfile 增加 BuildKit npm 缓存和最多三次 `npm ci --prefer-offline`，未修改锁文件或依赖版本。最终四服务均为 `healthy`。

真实 HTTP 验收：

- `GET /api/v1/health/ready`：`ready`；
- `POST /api/v1/assistant/query`：中文请求解析为头戴式、ANC、最高 1000 CNY，返回 2 件且全部满足硬条件；
- 首轮工具步骤 2，引用校验通过，证据项 30；
- 同会话“清除预算”后，类型与 ANC 继承，最高价格和币种被清除；Redis 会话读取一致；
- `POST /api/v1/products/compare`：2 件商品统一字段对比成功；
- `GET /api/v1/traces/{id}`：轨迹 ID 一致；
- `GET http://localhost:3000`：200，生产页面包含阶段 6 Agent 界面；
- Web、API、PostgreSQL、Redis：全部 `healthy`。

## 已知限制

- 默认 Agent Provider 是确定性规则/证据选择替身，真实 HTTP LLM Provider 尚无可用端点实测。
- 当前会话以不透明 UUID 作为 bearer-like 标识，MVP 尚无账号认证；不应把会话 ID 公开给其他用户。
- Redis 不可用时本轮检索仍可返回，但跨轮条件与轨迹不能持久化。
- 数据仍为 24 件合成 Fixture，外部 200 商品因许可不明确继续延期。
- 阶段 7 才会补齐独立对比页、完整交互状态和更系统的端到端浏览器体验。

