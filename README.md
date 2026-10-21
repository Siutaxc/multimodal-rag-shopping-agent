# ShopLens（智选镜）

ShopLens 是面向耳机选购场景的可解释多模态 RAG 导购系统。阶段 1～9 已完成：确定性商品数据、文本/图片检索、有界 Agent、证据约束回答、完整前端、缓存/限流/熔断/可观测、5k/50k 合成规模测试，以及一键 Fixture 交付、完整文档和面试材料均已验收。首批 200 条外部商品样本因上游数据许可未明确而继续延期，不影响当前 24 件 CC0 Fixture 的可复现工程基线。

## 当前包含

- Next.js App Router + TypeScript + Tailwind CSS 导购首页、独立结果页、证据详情页、2～4 商品对比页和开发轨迹页。
- FastAPI + Pydantic Settings，带 OpenAPI 文档。
- PostgreSQL 16 + pgvector、Redis 7.4 的 Docker Compose。
- /health/live 与 /health/ready；后者真实检查 PostgreSQL、vector 扩展和 Redis。
- SQLAlchemy 2 领域模型与 Alembic 空库迁移。
- 24 件 CC0 人工耳机 Fixture，以及校验、单位归一化、去重、幂等导入和错误统计。
- 本地内容寻址图片存储适配器；Docker 数据由 D 盘命名卷持久化。
- 商品分页、详情与价格/品类/品牌/ANC/续航/颜色/编码等结构化过滤 API。
- PostgreSQL `tsvector` 存储列、GIN 索引和参数化 `POST /api/v1/search` 词法检索。
- BGE-M3 HTTP/HTTPS Provider 契约、确定性离线替身、版本化 1024 维向量与 HNSW cosine 索引。
- 词法/稠密/RRF/有限 Top-K 重排四种模式，Reranker 超时自动降级到 RRF。
- 30 条冻结词法查询 + 18 条语义查询，以及四组 Recall、Precision、nDCG、MRR、硬条件、空结果和延迟指标。
- API 与前端开发轨迹：各通道 Top K、融合/重排变化、模型版本、耗时和降级原因。
- 24 张 CC0 合成商品图、安全 raster 上传、无损 WebP 重编码、元数据清理和不透明 `asset_id`。
- SigLIP2 HTTP/HTTPS 契约、确定性像素替身、版本化 768 维图片向量与独立 HNSW。
- 纯图片召回和图文带权 RRF；图片故障时保留文字检索并明确提示降级。
- 12 条纯图片 + 12 条图文标注，以及图片、去图片和完整融合四组消融。
- 白名单自然语言条件 Schema 与确定性规则降级解析器；模型不生成 SQL 或工具策略。
- 最多四步的有界状态机，以及 `search_catalog`、批量详情和 2～4 商品对比工具。
- Redis 会话条件继承、覆盖、按字段清除和全部重置；会话与轨迹使用不透明 UUID。
- 商品事实/评论证据包、缺失值证据、结构化回答、跨商品引用校验和安全回退。
- 默认离线 Agent Fixture 与可选 HTTP/HTTPS Schema Provider；解析/回答超时保留确定性商品卡。
- 15 个多轮 Agent 场景、384 条结构化事实和 Agent/证据评测报告。
- 冻结 30+18 条早期查询并新增 102 条，形成 150 条四组文本消融；失败查询与负结果完整保留。
- 文本/图文搜索的版本化 Redis 响应缓存，返回可检查的 `X-ShopLens-Cache: HIT/MISS`，TTL 到期自动失效，Redis 故障时 fail-open。
- Redis 固定窗口 POST 限流、`Retry-After`、统一 Provider 超时/指数退避重试和 closed/open/half-open 熔断。
- JSON 请求日志、慢 SQL 指纹日志、低基数 Prometheus 计数器/直方图与 `GET /metrics`。
- Alembic `20260722_0005` 覆盖硬过滤和活动向量连接索引；文本/图片回填改为有界内存的 keyset 批处理。
- 5,000/50,000 条明确标记的合成规模数据，以及索引前后 P50/P95、构建成本和完整执行计划。
- 当前设备会话/结果恢复、条件清除、图片预览/删除、重试、空结果恢复、部分降级与引用不可用状态。
- Playwright 桌面/移动核心流程与可选真实 Compose HTTP 演示流。
- pytest、Vitest、Playwright、Ruff、mypy、ESLint、TypeScript strict 与 CI 配置。
- 一条命令完成 Compose 构建、迁移、Fixture 导入、双向量索引和 HTTP 交付烟测；CI 从空环境重复同一链路。
- 单机生产 Compose 覆盖、真实 Reranker 故障开关、架构/数据/API/评测/限制文档、四分钟演示及简历/STAR/问答材料。
- 全部浏览器/API 通信使用 HTTP/HTTPS，不使用 WebSocket。

## 环境要求

- Docker Desktop，且 docker compose 可用。
- Node.js >= 20.9 与 npm >= 10（用于 npm 命令入口、本地开发和检查；也可直接运行 PowerShell 启动脚本）。
- Python >= 3.12（仅本地开发和检查需要）。

默认 Fixture Provider 不需要 GPU 或模型 API Key。真实 BGE Provider 可通过 HTTP/HTTPS 端点和环境变量启用。

## 一条命令启动

默认配置已经内置安全的本地开发值；如需修改端口或密码，先复制环境变量样例：

~~~powershell
Copy-Item .env.example .env
~~~

构建并启动 Web、API、PostgreSQL/pgvector 和 Redis，随后自动迁移、幂等导入 24 件 Fixture、回填文本/图片向量并执行 HTTP 验收：

~~~powershell
npm run stack:fixture
~~~

不安装 Node.js 时可直接运行：

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap-fixture.ps1
~~~

命令结束时必须输出 `result: passed`，并写出 `evals/reports/stage9-fixture-smoke.json`。重复执行是安全的；已导入记录会计入 `skipped`，不会生成重复商品。只启动/重建容器而不导入时使用 `npm run stack:up`；单独复验已运行环境使用 `npm run verify:fixture`。

也可在宿主机开发环境单独执行迁移或数据任务：

~~~powershell
npm run db:migrate
npm run data:import:fixture
npm run data:index:text
npm run data:index:image
~~~

服务就绪后访问：

- Web：http://localhost:3000
- OpenAPI UI：http://localhost:8000/docs
- 进程存活：http://localhost:8000/api/v1/health/live
- 依赖就绪：http://localhost:8000/api/v1/health/ready
- 商品列表：http://localhost:8000/api/v1/products
- 结构化过滤：http://localhost:8000/api/v1/products?category=in_ear&price_max=500&anc=true
- 商品详情：`http://localhost:8000/api/v1/products/{product_id}`
- 文本检索：`POST http://localhost:8000/api/v1/search`，`mode` 可选 `lexical`、`dense`、`rrf`、`rerank`
- 图片上传：`POST http://localhost:8000/api/v1/assets/images`，请求体为 JPEG/PNG/WebP 原始字节
- 图片/图文检索：`POST http://localhost:8000/api/v1/multimodal-search`，传 `asset_id`、可选 `query` 和硬过滤
- Agent 导购：`POST http://localhost:8000/api/v1/assistant/query`，传 `message`、可选 `session_id` / `asset_id` 和显式硬过滤
- 商品对比：`POST http://localhost:8000/api/v1/products/compare`，传 2～4 个 `product_ids`
- 会话条件：`GET http://localhost:8000/api/v1/sessions/{session_id}`
- 开发轨迹：`GET http://localhost:8000/api/v1/traces/{trace_id}`（生产环境关闭）
- Prometheus 指标：http://localhost:8000/metrics

真实 Reranker 故障演示不修改数据库：`npm run demo:degradation:on` 启用不可达 HTTP Provider 并断言 RRF 回退，`npm run demo:degradation:off` 恢复 Fixture。完整四分钟流程见 [阶段 9 演示](docs/stage-9-demo.md)。

金额在 PostgreSQL 中使用 `numeric(12,2)`，HTTP JSON 中使用十进制字符串表示，避免二进制浮点误差。所有过滤均由白名单参数转换为参数化 SQLAlchemy 查询，不接受原始 SQL。

复核冻结的 30 条词法基线，或运行 48 条四组文本消融：

~~~powershell
npm run eval:lexical
npm run eval:text
npm run eval:multimodal
npm run eval:agent
npm run eval:stage8
npm run perf:stage8
~~~

报告位于 `evals/reports/`。`perf:stage8` 会在主库中创建固定名称的 UNLOGGED 基准表，测试完成后自动删除，不修改规范商品表。当前评测只适用于 24 件人工 Fixture，规模数据是合成复制，均不能外推为真实模型或生产效果。

停止服务但保留数据库卷：

~~~powershell
npm run stack:down
~~~

## 本地开发

安装后端与前端依赖：

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\services\api[dev]"
npm install
~~~

分别启动 API 和 Web（使用两个终端）：

~~~powershell
npm run dev:api
~~~

~~~powershell
npm run dev:web
~~~

本地开发时仍需通过 Compose 启动 PostgreSQL 与 Redis，或在 .env 中提供可访问的同类依赖。

## 质量检查

一次运行本阶段全部静态检查、单元测试和前端生产构建：

~~~powershell
npm run check
~~~

使用确定性 HTTP 拦截运行桌面与移动 Chrome 核心端到端测试，不依赖付费模型或外部服务：

~~~powershell
npm run test:e2e
~~~

服务启动后可显式运行真实 Compose Web/API 演示流：

~~~powershell
$env:SHOPLENS_E2E_LIVE = "1"
$env:SHOPLENS_E2E_EXTERNAL_WEB = "1"
$env:SHOPLENS_WEB_BASE_URL = "http://127.0.0.1:3000"
npm run test:e2e:live
~~~

真实基础设施集成测试默认跳过。服务启动后可显式运行；测试会创建并删除带 `shoplens_stage3_test_` 前缀的临时数据库，不修改主库商品数据：

~~~powershell
$env:SHOPLENS_RUN_INTEGRATION = "1"
python -m pytest services/api/tests/integration -m integration
~~~

## 环境变量

所有后端变量使用 SHOPLENS_ 前缀，浏览器可见变量使用 Next.js 要求的 NEXT_PUBLIC_ 前缀。完整默认值见 [.env.example](.env.example)。密钥不得提交到仓库；后续模型 Provider 也只会从环境变量读取密钥。

常用变量：

| 变量 | 默认值 | 用途 |
|---|---|---|
| SHOPLENS_APP_ENV | development | 运行档位 |
| SHOPLENS_CORS_ALLOWED_ORIGINS | 本机 Web 两个 HTTP origin | JSON 格式的浏览器允许来源 |
| SHOPLENS_DATABASE_URL | 本机 PostgreSQL | API 数据库连接 |
| SHOPLENS_REDIS_URL | 本机 Redis | API Redis 连接 |
| SHOPLENS_OBJECT_STORAGE_PATH | `data/storage` | 本地对象存储根目录 |
| SHOPLENS_DEPENDENCY_TIMEOUT_SECONDS | 2 | 单次依赖探针超时 |
| SHOPLENS_CACHE_TTL_SECONDS | 60 | 搜索响应缓存 TTL |
| SHOPLENS_RATE_LIMIT_REQUESTS | 120 | 单窗口允许的 POST 请求数 |
| SHOPLENS_RATE_LIMIT_WINDOW_SECONDS | 60 | 限流窗口秒数 |
| SHOPLENS_PROVIDER_RETRY_ATTEMPTS | 3 | 远程 Provider 最大尝试次数 |
| SHOPLENS_CIRCUIT_BREAKER_FAILURE_THRESHOLD | 3 | 连续失败打开熔断器的阈值 |
| SHOPLENS_SLOW_QUERY_THRESHOLD_MS | 100 | 记录慢查询指纹的阈值 |
| SHOPLENS_EMBEDDING_PROVIDER | fixture | `fixture` 或 HTTP BGE-M3 |
| SHOPLENS_EMBEDDING_MODEL_VERSION | fixture-semantic-v1 | 活动向量版本 |
| SHOPLENS_RERANKER_PROVIDER | fixture | `fixture` 或 HTTP BGE Reranker |
| SHOPLENS_IMAGE_EMBEDDING_PROVIDER | fixture | `fixture` 或 HTTP SigLIP2 |
| SHOPLENS_IMAGE_EMBEDDING_MODEL_VERSION | fixture-visual-v1 | 活动图片向量版本 |
| SHOPLENS_IMAGE_UPLOAD_MAX_BYTES | 5242880 | 单张上传字节上限 |
| SHOPLENS_AGENT_PROVIDER | fixture | `fixture` 或 HTTP/HTTPS Schema Provider |
| SHOPLENS_AGENT_MAX_TOOL_STEPS | 4 | 单次请求的硬工具步数上限 |
| SHOPLENS_AGENT_SESSION_TTL_SECONDS | 86400 | Redis 会话条件 TTL |
| SHOPLENS_RRF_K | 60 | RRF 排名常数 |
| NEXT_PUBLIC_SHOPLENS_API_BASE_URL | http://localhost:8000 | 浏览器访问 API 的 HTTP 地址 |
| NEXT_PUBLIC_SHOPLENS_SITE_URL | http://localhost:3000 | Open Graph / X 预览图的站点基址 |

## 仓库结构

~~~text
apps/web/            Next.js Web
services/api/        FastAPI API、配置和测试
services/api/migrations/  Alembic 迁移
data/fixtures/       可提交的确定性小样本
evals/               冻结基线、150 条扩展评测与 5k/50k 性能报告
infra/               Docker Compose 与 pgvector 初始化
scripts/             Windows 本地启动/停止脚本
docs/                架构、数据、API、评测、部署、演示和阶段验收说明
~~~

总设计与后续阶段边界见 [MULTIMODAL_RAG_SHOPPING_AGENT_BLUEPRINT.md](MULTIMODAL_RAG_SHOPPING_AGENT_BLUEPRINT.md)。
本机 Docker、pgvector、Redis、HTTP 服务与测试的完整实测结果见 [阶段 1 验收记录](docs/stage-1-validation.md)。
阶段 2 的设计边界和实测结果见 [阶段 2 说明](docs/stage-2.md)与[阶段 2 验收记录](docs/stage-2-validation.md)。
阶段 3 的检索设计和实测结果见 [阶段 3 说明](docs/stage-3.md)与[阶段 3 验收记录](docs/stage-3-validation.md)。
阶段 4 的文本 RAG 设计和实测结果见 [阶段 4 说明](docs/stage-4.md)与[阶段 4 验收记录](docs/stage-4-validation.md)。
阶段 5 的多模态检索设计和实测结果见 [阶段 5 说明](docs/stage-5.md)与[阶段 5 验收记录](docs/stage-5-validation.md)。
阶段 6 的有界 Agent、证据约束和实测结果见 [阶段 6 说明](docs/stage-6.md)与[阶段 6 验收记录](docs/stage-6-validation.md)。
阶段 7 的完整前端、浏览器体验和实测结果见 [阶段 7 说明](docs/stage-7.md)、[阶段 7 验收记录](docs/stage-7-validation.md)与[三分钟演示流程](docs/stage-7-demo.md)。
阶段 8 的韧性、可观测、扩展评测与性能结果见 [阶段 8 说明](docs/stage-8.md)、[阶段 8 验收记录](docs/stage-8-validation.md)、[150 条评测报告](evals/reports/stage8-text-ablation.md)与[规模性能报告](evals/reports/stage8-performance.md)。
阶段 9 的交付总览和验收见 [阶段 9 说明](docs/stage-9.md)与[阶段 9 验收记录](docs/stage-9-validation.md)。重点材料包括：[部署](docs/deployment.md)、[架构](docs/architecture.md)、[数据](docs/data.md)、[HTTP API 示例](docs/api.md)、[评测与数字溯源](docs/evaluation.md)、[图表](docs/diagrams.md)、[已知限制](docs/known-limitations.md)、[四分钟演示](docs/stage-9-demo.md)和[简历/STAR/高频问答](docs/resume-and-interview.md)。

## License

ShopLens is released under the [MIT License](LICENSE).

This license applies to original project code and other materials for which the
project authors own the necessary rights. Third-party dependencies, pretrained
models, and external product data remain subject to their respective licenses.
