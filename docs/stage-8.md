# 阶段 8：评测、性能与工程加固

## 范围

阶段 8 在不改写阶段 3～7 数据集、报告、检索语义、Agent 四步上限和证据规则的前提下，把可演示系统补强为可量化、可降级、可观测的工程实现。全部连接继续使用 HTTP/HTTPS；没有引入 WebSocket，也没有让模型接触 SQL 或硬条件判断。

## 150 条扩展评测

`evals/datasets/stage8_text_queries.json` 新增 102 条 CC0 合成回归查询：72 条商品身份查询、18 条对抗空结果和 12 条场景查询。运行时与冻结的阶段 3 词法 30 条、阶段 4 语义 18 条组合为 150 条；早期文件和报告均未修改。

`npm run eval:stage8` 对 lexical、dense、RRF、rerank 四种模式运行相同查询，自动输出 Markdown/JSON。报告保留每条期望/返回 ID、延迟、降级原因、硬条件违反和完整失败 ID，不因指标不佳删除样本。当前确定性 Fixture 的结果中，RRF 优于重排；这是一项保留的负结果，不代表真实 BGE-M3 或 BGE Reranker 质量。

## 缓存与限流

文本和图文搜索使用 Redis 响应缓存。键由规范化请求、缓存命名空间及文本、重排、图片模型版本共同计算，不记录原始查询到日志；响应返回 `X-ShopLens-Cache: HIT` 或 `MISS`。默认 TTL 为 60 秒，版本变化或命名空间变化自然切换键空间；Redis 不可用、值损坏或写入失败时搜索 fail-open，不用缓存阻断核心检索。

固定窗口限流保护 POST/PUT 路径。客户端地址先经 SHA-256 截断后进入 Redis 键，避免存储原始地址；默认每 60 秒 120 次。超限返回 HTTP 429 和 `Retry-After`。Redis 不可用时限流 fail-open，同时增加降级指标，避免缓存依赖故障扩大成全站不可用。

## Provider 韧性

文本 Embedding、Reranker、图片 Embedding 和 Agent HTTP Provider 共享同一套韧性原语：

- 每次 HTTP 请求仍受原有 Provider 超时控制；
- 只对网络错误、超时、HTTP 429 和 5xx 做最多三次有界指数退避；
- 非重试型 4xx 和无效响应直接失败；
- 连续三次最终失败后打开跨请求共享的熔断器；30 秒后仅允许一个 half-open 探针；
- 熔断拒绝具有单独降级原因，文本回退词法/RRF、图文回退文字、Agent 回退规则解析或安全证据计划。

默认 Fixture Provider 不经过远程 HTTP，因此 CI 不依赖付费接口。

## 数据库和批量推理

Alembic `20260722_0005` 增加：

- `products(category, currency, anc, wireless, price_amount, id)` 硬过滤覆盖索引；
- 活动文本向量版本到 `document_id` 的 partial covering index；
- 活动图片向量版本到 `image_id` 的 partial covering index。

文本和图片向量回填从一次性加载全部记录改为 UUID keyset 分页。每批读取、推理、记录逐批失败并提交，内存占用由总商品量改为批大小约束；模型、维度、表示/文档版本和源哈希审计规则保持不变。

## 可观测性

API 为每个请求生成或校验 `X-Request-ID`，输出一条 JSON 访问事件，只记录方法、UUID 归一化路径、状态和耗时。SQLAlchemy Engine 记录语句类型、耗时与 SHA-256 查询指纹；达到 `SHOPLENS_SLOW_QUERY_THRESHOLD_MS` 才输出慢查询事件，不记录 SQL 文本、绑定参数、查询内容、会话 ID 或密钥。

`GET /metrics` 以 Prometheus 0.0.4 文本格式提供：

- HTTP 请求数和耗时直方图；
- 数据库语句数、耗时和慢查询数；
- 缓存命中/未命中及 Redis 错误；
- 限流拒绝和限流存储降级；
- Provider 成功/失败、重试与熔断拒绝。

路径 UUID 被归一化，标签集合固定，避免商品、会话或查询内容造成高基数。

## 5k/50k 合成规模测试

`npm run perf:stage8` 创建固定名称的 UNLOGGED 基准表，从 24 件 CC0 Fixture 复制并扰动非关键字段，明确标记为 synthetic。脚本分别装载 5,000 和 50,000 行，对结构化过滤、PostgreSQL FTS 和 pgvector ANN 在索引前后各预热三次并测量 20 次，保存 P50/P95 及 `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`。

基准表默认在 `finally` 中删除，不修改规范 `products`、文档、证据或向量表。重复 Fixture 向量只适合验证索引与执行路径，不代表真实商品分布或真实检索质量。

## 已知边界

- 150 条查询仍由项目作者围绕 24 件 Fixture 构造，不是独立标注的开放域测试集。
- 真正的 BGE-M3、SigLIP2 和 Agent HTTPS 端点仍不可用；当前只验证契约、重试、熔断和降级。
- 单进程自建 Prometheus 累加器适合当前单 API 容器；多 worker 部署需切换到支持 multiprocess 聚合的实现。
- TTL 内的商品写入可能短暂读取旧搜索缓存；当前没有在线商品写 API，批量导入后可更换缓存命名空间或等待最多 60 秒。
- 限流按 API 看到的客户端地址工作；部署在反向代理后必须由受信代理统一网络入口，当前实现不会直接信任任意 `X-Forwarded-For`。
