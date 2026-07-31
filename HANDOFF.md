# ShopLens 项目交接文档

最后更新：2026-07-23  
实际工作区：`D:\CodexProjects\bytedance`

## 0. 下一窗口先看这里

接手后按以下顺序阅读：

1. 本文件 `HANDOFF.md`。
2. `MULTIMODAL_RAG_SHOPPING_AGENT_BLUEPRINT.md`，它是项目唯一总控文档。
3. `docs/stage-9-validation.md` 与 `docs/stage-9.md`，确认一键启动、干净环境、生产覆盖、浏览器和交付验收。
4. `docs/deployment.md`、`docs/architecture.md`、`docs/api.md` 与 `docs/evaluation.md`，确认运行方式、系统边界、接口示例和数字溯源。
5. `docs/stage-9-demo.md` 与 `docs/resume-and-interview.md`，确认四分钟演示、真实降级、简历/STAR 和高频问答。
6. `evals/reports/stage9-fixture-smoke.json` 与 `stage9-production-smoke.json`，确认主环境和独立新环境 HTTP 烟测。
7. `docs/stage-8-validation.md` 与 `docs/stage-8.md`，确认 150 条评测、韧性、可观测和 5k/50k 性能验收。
8. `evals/reports/stage8-text-ablation.md` 与 `evals/reports/stage8-performance.md`，确认失败样本、负结果、P50/P95 和瓶颈。
9. `docs/stage-7-validation.md`、`docs/stage-6-validation.md` 和阶段 5/4/3 报告，仅在追溯冻结基线时再看。
10. `README.md`，确认启动、检查、评测和 Playwright 命令。

当前阶段结论：**阶段 1～9 均已验收完成，总控蓝图全部闭环。** 不要重做阶段 1～9；项目没有自动开始的阶段 10，后续只按用户明确要求处理真实数据/模型、认证、多副本或依赖漏洞定向升级。

## 1. 我们在做什么

项目名：**ShopLens（智选镜）多模态 RAG 电商导购 Agent**。

目标是做一个面向耳机选购、可解释且可评测的导购系统：

- 自然语言条件搜索，覆盖预算、佩戴方式、降噪、续航和使用场景；
- 支持以图搜商品及图文混合搜索；
- 2～4 个商品结构化对比；
- 推荐理由、价格、参数和评论结论必须有可追溯证据；
- 预算、品类、ANC 等硬条件由确定性代码和数据库过滤保证，不能交给 LLM 猜测。

技术路线：Next.js + FastAPI + PostgreSQL/pgvector + Redis，逐阶段加入词法检索、文本/图片向量、融合、重排和有界 Agent。

所有本地和远程连接只使用 HTTP/HTTPS，不使用 WebSocket。未来如需流式输出，只能考虑 HTTP SSE。

## 2. 已经完成了什么

### 2.1 环境与阶段 1

- Windows 11 25H2、WSL 2.7.10.0 和 Docker Desktop 4.83.0 已修复并验收。
- Docker 主程序在 `D:\Apps\DockerDesktop`，数据根目录在 `D:\DockerData`；不要移回 C 盘。
- Compose 包含 Web、API、PostgreSQL 16 + pgvector 0.8.5、Redis 7.4，四服务均真实运行。
- FastAPI 就绪探针、OpenAPI、Next.js App Router、严格类型、测试和生产构建链路均已完成。

### 2.2 阶段 2：确定性商品数据

- SQLAlchemy 2 ORM 与 Alembic `20260722_0001` 建立商品、图片、文档、评论证据和摄取任务表。
- `data/fixtures/headphones.json` 包含 24 件 CC0 人工耳机商品。
- 摄取支持严格 Schema、金额精度、UTC 时间、单位与枚举归一化、去重、幂等跳过/更新和逐记录错误报告。
- `LocalObjectStorage` 使用 SHA-256 内容寻址和原子写入。
- `GET /api/v1/products` 与详情 API 支持参数化结构化过滤并保留来源和价格观测时间。
- 主库首次导入 24 成功，第二次导入 24 跳过，商品数保持 24。

首批 200 件外部商品仍未导入：Amazon Reviews 2023 可查数据卡没有明确数据许可，代码仓库 MIT 许可不能推定覆盖商品、评论或图片。该项继续延期；不得下载全量数据、伪造来源或声称已完成。

### 2.3 阶段 3：PostgreSQL 词法基线

- Alembic `20260722_0002` 为 `product_documents` 增加事实限定的 `search_text`、存储生成的 `search_vector` 和 GIN 索引。
- 阶段 2 主库已原位升级到 `20260722_0002`；24 件商品和两次摄取记录完整保留，24 个文档全部完成向量回填。
- 词法文档版本为 `stage3-lexical-v1`，覆盖品牌、完整标题/型号、品类、可审查的中英别名和已有结构化参数；缺失值不补猜。
- 已实现 `POST /api/v1/search`：PostgreSQL `websearch_to_tsquery` + `ts_rank_cd` + 白名单硬过滤 + 稳定同分排序。用户输入不拼接 SQL。
- API 明确返回 `retrieval_mode`、`search_document_version`、`lexical_score`、排名、实际过滤和分页信息。
- `evals/datasets/stage3_lexical_queries.json` 有 30 条固定 `source_id` 标注查询，覆盖精确型号、品牌、参数、中文场景、多硬条件和空结果。
- 评测器计算 Recall@5/10、Precision@5、nDCG@10、MRR、硬条件违反率和空结果准确率，并输出 Markdown/JSON。
- 前端已完成“搜索 → 结果列表 → 商品详情”，显示结构化事实、词法分、价格时间戳和 HTTPS 来源链接。
- 阶段 3 当时没有实现 Embedding、向量召回、HNSW 或 Reranker；这些文本能力现已在阶段 4 完成。LLM 条件解析和 Agent 仍未实现。

### 2.4 阶段 4：文本 RAG

- Alembic `20260722_0003` 新增版本化 `text_embeddings`，持久化模型名、模型版本、1024 维度、稠密/来源文档版本、内容哈希、生成时间、状态与失败原因。
- 建立 `vector_cosine_ops` 的 partial HNSW 索引，只索引 `ready` 向量；查询按完整版本身份精确选择，不混用旧模型记录。
- `EmbeddingProvider` 与 `RerankerProvider` 均有确定性离线 Fixture 替身和 HTTP/HTTPS BGE 适配器；不使用 WebSocket，密钥只读环境变量。
- 批处理支持内容哈希幂等、逐批失败记录、同版本失败重试和新版本并存。主库 24 个默认活动文本向量已生成。
- `POST /api/v1/search` 支持 `lexical`、`dense`、`rrf`、`rerank` 四种模式；词法和稠密通道复用同一白名单硬过滤。
- RRF 的通道 Top K、融合 Top K、重排 Top K 和 `rrf_k` 可配置并写入轨迹/报告。
- Reranker 只处理有限候选，超时或错误返回不变 RRF 顺序和 `hybrid_rrf_fallback`。
- API/前端开发轨迹展示各通道 Top K、融合与重排排名变化、阶段耗时、模型版本、文档版本和降级原因。
- 阶段 3 的 30 条标注文件保持不变；阶段 4 额外增加 18 条语义/空结果查询，共 48 条四组消融。
- 阶段 4 文本 Provider、数据集和报告保持冻结，阶段 5 没有改写失败查询来制造提升。

### 2.5 阶段 5：多模态检索

- Alembic `20260722_0004` 新增 `image_embeddings` 与 `uploaded_image_assets`，图片向量精确绑定模型名、版本、768 维、表示版本和源图片哈希。
- 图片 HNSW 只索引 `ready` 记录；主库 24 个商品图片和 24 个默认活动图片向量已生成，失败重试与三版本并存已在临时空库验证。
- `ImageEmbeddingProvider` 有确定性像素 Fixture 替身和 HTTP/HTTPS SigLIP2 适配器；真实端点尚未实测，不得把 Fixture 指标称为 SigLIP2 指标。
- `POST /api/v1/assets/images` 对原始 HTTP 图片体执行字节、MIME、解码、动画、像素和尺寸校验，应用方向后重编码为无损 WebP 并清除元数据，返回不透明 `asset_id`。
- `POST /api/v1/multimodal-search` 支持纯图片和图片 + 文字；图片与文本原始相似度保持独立，只按通道排名做带权 RRF。
- 图片与文本通道复用同一组参数化硬过滤；图片 Provider 失败时图文查询降级到文本，纯图片查询返回明确不可用状态。
- 增加 12 条纯图片 + 12 条图文标注，报告纯图、混合仅图、混合仅文和完整融合四组消融；完整融合低于文本消融的负结果已保留。
- 前端支持输入方式、图片预览、安全上传、纯图/图文结果、通道分数、开发轨迹、错误与降级提示。

### 2.6 阶段 6：有界导购 Agent 与证据回答

- 新增严格 `ParsedTurn` 白名单 Schema、确定性中文规则解析器与可选 HTTP/HTTPS Agent Provider；模型不能生成 SQL 或工具策略。
- 实现最多 4 步的代码固定状态机，当前流程只开放会话读取、商品检索、批量详情和 2～4 商品对比；实测最大 3 步。
- Redis 按不透明 UUID 隔离会话与开发轨迹，支持硬条件继承、最新值覆盖、按字段清除和全部重置。
- 商品事实、评论和缺失值形成结构化证据包；模型只选择证据 ID，价格、参数、对比单元格和回答文本由确定性代码渲染。
- 引用校验拒绝未知、跨商品和字段不一致引用；失败时安全回退到商品价格事实。
- 商品描述与评论始终是非可信数据，不能改变工具策略；解析/回答超时仍返回已取得的确定性商品卡和明确降级。
- 新增 `POST /assistant/query`、`POST /products/compare`、`GET /sessions/{id}` 与非生产 `GET /traces/{id}`。
- 首页默认进入 Agent 导购模式，展示会话条件、证据链接、状态机、工具步骤、引用校验和降级，同时保留阶段 3～5 检索入口。
- 新增 15 个多轮 Agent 场景和 384 条结构化事实评测；首轮发现并修复续航“至少”误判为最低价格的问题，未改写失败查询。

### 2.7 阶段 7：完整前端与端到端体验

- 新增独立 `/results`、`/compare` 和 `/traces/{id}` 页面，并强化 `/` 与 `/products/{id}`；四种输入、证据定位、2～4 商品对比和开发轨迹均可从 UI 完成。
- 最近结构化结果、查询草稿、对比清单和不透明会话标识只保存在当前设备；刷新恢复结果并通过会话端点校验，不把 `session_id` 写入 URL。
- 支持条件单字段清除、图片预览/删除、重新提交、空结果恢复、超时、HTTP/网络错误、会话失效、部分降级和引用不可用状态。
- 商品事实、推荐理由、对比单元格和引用全部直接读取结构化响应；详情页用 `fact-*` / `review-*` 锚点定位，不解析自然语言答案。
- 完成桌面、平板和移动布局，补齐跳过链接、键盘焦点、live region、语义表格、图片替代文本、高对比和减弱动画。
- 新增 Playwright：默认确定性桌面/移动核心用例 10/10；显式连接 Compose 的真实 HTTP 桌面/移动演示流 2/2。
- 真实多模态浏览器流发现并修复轨迹结构差异：文本轨迹顶层 `rerank`，多模态轨迹使用 `text_trace.rerank`；后端契约未改动。

### 2.8 阶段 8：评测、性能与工程加固

- 保持阶段 3/4 冻结的 30+18 条查询不变，新增 102 条商品身份、对抗空结果和场景查询，形成 150 条四组消融。
- RRF 在当前 Fixture 上最佳：Recall@10 0.9821、nDCG@10 0.9464；重排没有超过 RRF，负结果与 17/31 个失败 ID 完整保留。
- 文本/图文搜索新增版本化 Redis 缓存，实测 MISS → HIT → TTL 后 MISS；Redis 故障 fail-open。
- 新增 Redis 固定窗口限流，实测窗口内第 121 个 POST 返回 429 和 `Retry-After`；限流存储故障 fail-open。
- 四类远程 Provider 统一使用超时、有界指数退避重试和跨请求 closed/open/half-open 熔断，具有独立降级原因。
- Alembic `20260722_0005` 增加硬过滤与活动向量连接覆盖索引；文本/图片向量回填改为 keyset 有界批处理。
- 新增 JSON 请求日志、慢 SQL 指纹、Prometheus 请求/数据库/缓存/限流/Provider 指标和 `GET /metrics`。
- 完成 5k/50k 明确合成规模测试。50k 索引前结构化/词法/ANN P95 为 23.389/39.634/239.207 ms，索引后为 0.462/10.681/1.113 ms；完整执行计划和构建成本已保存。
- Compose 重建已包含阶段 8 API 与阶段 7 `public/og.png`；`/og.png` 现返回 200。

### 2.9 阶段 9：部署、文档与面试交付

- 新增 `npm run stack:fixture`：Compose 构建/健康等待、容器内迁移、24 件幂等导入、文本/图片向量和 HTTP 烟测一条命令完成；`verify:fixture` 单独复验并生成 JSON。
- 新增生产 Compose 覆盖：隐藏 PostgreSQL/Redis 宿主端口，API/Web 使用非 root、只读根、capabilities 删除、`no-new-privileges`、tmpfs、日志轮转与资源上限；真实独立空卷启动验收通过。
- Python、Node、pgvector、Redis 基础镜像固定为可读标签 + 本轮验收 manifest SHA-256；本机所有端口和默认 DSN 对齐 `127.0.0.1`。
- 新增真实 Reranker HTTP 故障档位，实测回退 `hybrid_rrf_fallback`、原因 `reranker_error`，商品与硬条件保留；恢复命令复验通过且不修改数据库。
- 完成部署、架构、数据、API 示例、评测/数字溯源、图表、已知限制、四分钟演示、简历/STAR 和高频问答文档。
- 独立全新项目首次导入 24/24、文本/图片索引各 24/24，生产覆盖 HTTP 烟测 passed；烟测资源已清理，报告保留。

### 2.10 最终实测结果

- `npm run check` 完整通过。
- Ruff、mypy strict、ESLint、TypeScript strict：全部通过。
- 后端单元测试：183 通过，2 个集成测试按标记排除；其中包含 100 条逐价格事实精确性、阶段 8 故障注入和阶段 9 回环 DSN 防回归用例。
- PostgreSQL/Redis 集成测试：2 通过；临时空库完整执行 `0001 → 0005`、`alembic check`、摄取、keyset 双向量回填、阶段 4/5 评测及 Agent 会话、轨迹、对比和真实 HTTP API。
- 前端 Vitest：9 通过；Playwright 确定性核心用例 10 通过，真实 Compose 用例 2 通过；Next.js 生产构建通过。
- Compose API/Web 最终镜像重建通过；Web、API、PostgreSQL、Redis 均为 `healthy`。
- 真实 HTTP：就绪状态 `ready`；Agent 中文查询解析头戴式/ANC/1000 CNY，返回 2 件且全部满足硬条件，工具 2 步、引用校验通过、证据 30；同会话清除预算后保留类型和 ANC；2 商品对比、会话和轨迹读取成功；Web 返回 200。
- 主库：迁移版本 `20260722_0005`，商品 24，默认活动文本向量 24、图片 24、默认活动图片向量 24，GIN、文本/图片 HNSW 与阶段 8 covering indexes 均存在。

阶段 3 基线（24 件人工 Fixture、30 条定制工程回归查询）：

| 指标 | 实测值 |
|---|---:|
| Recall@5 | 0.9844 |
| Recall@10 | 1.0000 |
| Precision@5 | 0.4552 |
| nDCG@10 | 1.0000 |
| MRR | 1.0000 |
| 硬条件违反率 | 0.0000 |
| 空结果准确率 | 1.0000 |

高指标只证明确定性小样本回归正确，不能包装为真实商品库或开放域中文检索效果。

阶段 4 四组消融（同一 24 件 Fixture、30 条冻结查询 + 18 条新增语义查询）：

| 模式 | Recall@5 | Recall@10 | Precision@5 | nDCG@10 | MRR | 硬条件违反率 |
|---|---:|---:|---:|---:|---:|---:|
| 词法 | 0.6206 | 0.6304 | 0.2870 | 0.6304 | 0.6304 | 0.0000 |
| 稠密 | 0.9233 | 0.9791 | 0.4087 | 0.9239 | 0.9227 | 0.0000 |
| RRF | 0.9394 | 0.9928 | 0.4261 | 0.9648 | 0.9589 | 0.0000 |
| 重排 | 0.9233 | 0.9791 | 0.4087 | 0.9239 | 0.9227 | 0.0000 |

RRF 是当前确定性 Fixture 替身下的最佳组；重排没有超过 RRF，负结果已保留。默认替身只证明工程链路，不代表真实 BGE-M3 / bge-reranker-v2-m3 质量。

阶段 5 四组消融（24 件 Fixture、12 条纯图片 + 12 条图文查询）：

| 模式 | Recall@5 | Recall@10 | Precision@5 | nDCG@10 | MRR | 硬条件违反率 |
|---|---:|---:|---:|---:|---:|---:|
| 纯图片 | 1.0000 | 1.0000 | 0.7091 | 0.9809 | 1.0000 | 0.0000 |
| 混合仅图片 | 1.0000 | 1.0000 | 0.2909 | 0.9090 | 0.8939 | 0.0000 |
| 混合仅文本 | 1.0000 | 1.0000 | 0.2909 | 0.9755 | 1.0000 | 0.0000 |
| 完整图文融合 | 1.0000 | 1.0000 | 0.2909 | 0.9037 | 0.8939 | 0.0000 |

完整融合没有超过文本消融；合成图过于规则、文字查询已很明确且图片权重尚未在真实数据上校准。该结果只证明多模态工程链路，不代表真实 SigLIP2 质量。

阶段 6 Agent/证据评测（24 件 Fixture、15 个多轮场景）：

| 指标 | 实测值 |
|---|---:|
| 任务完成率 | 1.0000 |
| 工具选择正确率 | 1.0000 |
| 引用精确率 / 覆盖率 | 1.0000 / 1.0000 |
| 结构化事实条数 | 384 |
| 结构化事实幻觉率 | 0.0000 |
| 条件修改正确率 | 1.0000 |
| 平均 / 最大工具调用 | 2.200 / 3 |
| 无效循环率 | 0.0000 |
| 完整回答 P50 / P95 | 26.303 / 138.085 ms |

这些指标来自确定性 Fixture Agent 和人工小样本，只证明 Schema、工具边界、证据和降级链路，不代表真实 LLM 质量。

## 3. 当前卡在哪里

**阶段 1～9 没有未关闭的验收阻塞。** 阶段 9 已完成。

仍需知道的状态：

1. 外部 200 条商品是已知延期项，但不应冒充完成，也不应再次阻塞已验收的阶段 8。
2. 工作区根目录存在无效/空 `.git` 目录，`git rev-parse` 仍会报告不是 Git 仓库。本轮没有初始化或删除它。
3. 当前 Windows 登录令牌可能无法让普通 PowerShell 直接访问 Docker 命名管道；必要时使用 `D:\Apps\DockerDesktop\resources\bin\docker.exe` 并把该目录临时加入 `PATH`。
4. 阶段 9 容器 `npm ci` 汇总报告构建依赖图有 1 个 moderate、2 个 high；没有运行 `npm audit fix --force`。如用户要求加固，按具体 advisory 定向升级、重建并复验，不能把 build-stage 依赖数直接等同于 standalone 运行镜像暴露面。
5. 阶段 4/5/6 默认模型都是确定性离线替身，真实 HTTP/HTTPS BGE、SigLIP2 和 Agent 适配器已通过契约测试但尚无可用端点实测；不得把 Fixture 指标称为真实模型指标。
6. 首次回填发现一对合成图哈希重复，数据库约束正确拒绝；生成器已修复为 24 个唯一哈希，失败记录保留在摄取任务中。
7. 阶段 7 遗留的 `/og.png` 404 已随阶段 8 Compose 重建关闭，当前返回 200。API/Web/PostgreSQL/Redis 均为 `healthy`。
8. Prometheus 累加器适用于当前单 API 容器；若改为多 worker，需换用支持 multiprocess 聚合的实现。
9. 缓存 TTL 内的离线商品导入最多产生 60 秒旧搜索结果；当前没有在线写 API，导入后可切换 `SHOPLENS_CACHE_NAMESPACE` 或等待 TTL。

## 4. 后续仅按用户明确要求推进

总控文档阶段 1～9 已全部完成，没有预定义阶段 10。可选后续工作按优先级为：

1. 针对 `npm ci` 报告的具体 advisory 做非破坏性、定向依赖升级，生成 SBOM/镜像扫描报告并全量复验。
2. 获得明确数据许可证后，建立独立标注的真实商品集；不得覆盖阶段 3～8 冻结报告。
3. 接入真实 HTTPS BGE-M3、Reranker、SigLIP2 或 Agent Provider，新建模型版本与质量报告。
4. 增加账号/租户授权、HTTPS 反向代理、共享对象存储、备份恢复、并发/长稳和生产 SLO。
5. 多 worker/多副本前替换 Prometheus 聚合方式，并设计共享限流/熔断语义。

不要在没有用户要求时自动开始这些可选项；阶段 3～9 的数据集和报告现在都作为不可改写基线。

## 5. 常用命令和端点

工作目录：

~~~powershell
Set-Location "D:\CodexProjects\bytedance"
~~~

一条命令构建、启动、导入、双向量索引并执行 HTTP 验收：

~~~powershell
npm run stack:fixture
~~~

迁移、Fixture 导入、文本/图片向量与评测：

~~~powershell
npm run db:migrate
npm run data:import:fixture
npm run data:index:text
npm run data:index:image
npm run eval:lexical
npm run eval:text
npm run eval:multimodal
npm run eval:agent
npm run eval:stage8
npm run perf:stage8
~~~

完整检查与真实 PostgreSQL/Redis 集成测试：

~~~powershell
npm run check
$env:SHOPLENS_RUN_INTEGRATION="1"
python -m pytest services/api/tests/integration -q
npm run test:e2e
$env:SHOPLENS_E2E_LIVE="1"
$env:SHOPLENS_E2E_EXTERNAL_WEB="1"
$env:SHOPLENS_WEB_BASE_URL="http://127.0.0.1:3000"
npm run test:e2e:live
~~~

端点：

- Web：`http://localhost:3000`
- API 文档：`http://localhost:8000/docs`
- 就绪检查：`http://localhost:8000/api/v1/health/ready`
- 商品列表：`GET http://localhost:8000/api/v1/products`
- 商品详情：`GET http://localhost:8000/api/v1/products/{product_id}`
- 文本搜索：`POST http://localhost:8000/api/v1/search`；`mode` 为 `lexical` / `dense` / `rrf` / `rerank`
- 图片上传：`POST http://localhost:8000/api/v1/assets/images`；请求体为 JPEG / PNG / WebP 原始字节
- 图片/图文搜索：`POST http://localhost:8000/api/v1/multimodal-search`；传 `asset_id`、可选 `query` 与硬过滤
- Agent 导购：`POST http://localhost:8000/api/v1/assistant/query`；传 `message`、可选 `session_id` / `asset_id` 和硬过滤
- 商品对比：`POST http://localhost:8000/api/v1/products/compare`；传 2～4 个 `product_ids`
- 会话条件：`GET http://localhost:8000/api/v1/sessions/{session_id}`
- 开发轨迹：`GET http://localhost:8000/api/v1/traces/{trace_id}`；生产环境关闭
- Prometheus 指标：`GET http://localhost:8000/metrics`

若旧终端中 Docker CLI/凭据工具找不到：

~~~powershell
$env:PATH="D:\Apps\DockerDesktop\resources\bin;$env:PATH"
& "D:\Apps\DockerDesktop\resources\bin\docker.exe" version
~~~

## 6. 绝对不要再踩的坑

1. 不要安装 Ubuntu、反复运行 `wsl --install`，也不要重做已完成的 Windows Update/WSL 修复。
2. 不要运行曾破坏 Windows Update ACL 的联想“关闭 Win11 系统自动更新”工具。
3. 不要把 Docker 移回 C 盘，不要手工移动/删除 VHDX，也不要删除 `C:\Program Files\Docker\cli-plugins`。
4. 不要把 Compose 构建上下文从 `.` 改回 `..`，也不要改坏 pgvector 初始化脚本路径。
5. 不要恢复 Web Dockerfile 对 `apps/web/node_modules` 的错误 COPY；npm workspace 依赖在根目录提升。
6. 不要在 Windows 上把就绪探针改回 psycopg `AsyncConnection`，除非同时解决 Proactor 兼容问题。
7. 不要使用 WebSocket；本项目所有连接使用 HTTP/HTTPS。
8. 不要让 LLM 生成/执行 SQL 或判断硬条件；过滤必须由白名单 Schema 和参数化数据库查询保证。
9. 不要下载全量 Amazon Reviews 商品/图片，不要伪造外部 200 条样本；许可明确前保持延期。
10. 不要为了提高小样本指标修改阶段 3 相关性标注、删除失败查询或把指标包装成生产效果。
11. 不要让任何阶段混用不同模型、维度、文档版本的向量；版本与来源必须持久化并可审计。
12. 不要把阶段 4 的确定性 Fixture Provider 指标包装成真实 BGE 模型效果；真实 Provider 尚未实测。
13. 不要初始化或删除无效 `.git` 目录，除非用户明确要求。
14. 不要运行 `npm audit fix --force`。
15. 不要在阶段 5 把图片与文本原始相似度直接相加，也不要让图片模型判断价格、ANC、品类等硬条件。
16. 不要把阶段 6 改成开放式 ReAct 循环；最大工具步数必须保持硬上限 4，模型只能解析 Schema 和选择证据 ID。
17. 不要让商品描述、评论或图片 OCR 决定工具策略；它们始终是不可信数据。
18. 不要从自然语言答案反向解析商品、价格或证据；前端必须读取结构化字段。
19. 不要把不透明 `session_id` 记录到公开页面或分享给其他用户；当前 MVP 尚无账号认证。

## 7. 交接结论

阶段 1～9 已闭环。当前系统具备 PostgreSQL 词法、文本/图片 pgvector 召回、参数化硬过滤、版本化双向量、独立 HNSW、RRF、有限重排、安全图片上传、纯图/图文检索、最多四步的有界 Agent、Redis 会话条件、2～4 商品对比、结构化证据、引用校验、提示注入隔离、模型超时降级、150 条消融、版本化缓存、限流、重试/熔断、结构化日志、Prometheus 指标、慢查询指纹、keyset 批处理、覆盖索引、5k/50k 性能报告、完整多路由前端、证据深链、桌面/移动 Playwright，以及固定基础镜像摘要、一键 Fixture、单机生产覆盖、真实降级开关、全套架构/API/评测/限制文档和简历/STAR/问答材料。总控蓝图已全部完成；下一窗口不要自动开启新阶段，只按用户明确要求处理可选加固。阶段 3～9 报告均作为不可改写基线。
