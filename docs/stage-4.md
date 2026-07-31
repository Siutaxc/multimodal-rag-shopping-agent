# 阶段 4：文本 RAG——稠密召回、融合与重排

日期：2026-07-22  
范围：版本化文本向量、pgvector HNSW、稠密召回、RRF、有限 Top-K 重排、开发轨迹与四组消融

## 范围与边界

阶段 4 只实现文本通道，不包含图片向量、图片上传、以图搜商品、图文混合检索、LLM 条件解析或 Agent。预算、品类、ANC、续航等硬条件继续由阶段 2/3 的白名单 Schema 和参数化 SQLAlchemy 条件执行，词法与稠密通道使用同一组过滤子句。

当前语料仍是 24 件 CC0 人工 Fixture。外部 200 条样本因数据许可未明确继续延期。默认 Embedding/Reranker 是确定性离线替身，用于 CI、回归和无密钥演示；报告不能解释为真实 BGE-M3 或 Cross-Encoder 的线上质量。

所有 Provider 通信只支持 HTTP/HTTPS，不使用 WebSocket。

## Provider 契约

`app.providers.retrieval` 定义：

- `EmbeddingProvider`：批量接收文本并返回固定维度向量；身份包含模型名、模型版本和维度。
- `RerankerProvider`：接收查询和有限文档列表，按输入顺序返回相关性分数。
- `BgeM3HttpEmbeddingProvider`：通过 HTTP/HTTPS 调用 OpenAI-compatible embedding JSON 接口。
- `BgeRerankerHttpProvider`：通过 HTTP/HTTPS 调用 BGE rerank JSON 接口。
- `DeterministicEmbeddingProvider` / `DeterministicRerankerProvider`：固定、离线、可复现的 Fixture 替身。

HTTP 适配器校验端点协议、响应数量、维度、数值有限性和超时。密钥只从 `SHOPLENS_*_API_KEY` 环境变量读取。Fixture 模式允许 Compose 把未配置的可选地址/密钥传为空字符串，并在配置层规范化为 `None`。

## 版本化文本向量与 HNSW

Alembic `20260722_0003` 新增 `text_embeddings`：

- `document_id` 与来源商品主文档；
- `model_name`、`model_version`、`dimension`；
- `document_version=stage4-dense-v1` 与 `source_document_version`；
- `content_sha256`、`generated_at`、`status`、`last_error`；
- `vector(1024)` 文本向量。

唯一键覆盖“文档 + 模型名 + 模型版本 + 维度 + 稠密文档版本”。查询必须精确匹配这组身份和 `ready` 状态，因此模型版本切换不会读取旧向量。`ix_text_embeddings_hnsw_cosine` 使用 `vector_cosine_ops`，仅索引 `ready` 记录。

稠密文档只组合已持久化的商品事实和评论证据，不生成新事实。批处理器按内容 SHA-256 幂等跳过；失败记录保存原因并可用相同版本重试；新模型版本写入新记录，不覆盖旧版本。

~~~powershell
npm run db:migrate
npm run data:index:text
~~~

## 检索、融合、重排与降级

`POST /api/v1/search` 的 `mode` 支持：

- `lexical`：PostgreSQL FTS；
- `dense`：精确版本的 pgvector cosine 召回；
- `rrf`：词法与稠密按 `1 / (rrf_k + rank)` 融合；
- `rerank`：对 RRF 的有限 Top K 执行 Reranker，默认模式。

默认参数为词法 Top 50、稠密 Top 50、融合 Top 30、重排 Top 30、`rrf_k=60`，全部由环境配置并写入查询轨迹和评测报告。Reranker 超时或错误返回不变的 RRF 顺序，`retrieval_mode=hybrid_rrf_fallback`，同时记录 `degraded_reason`。

响应中的每个商品可包含词法排名/分数、稠密排名/相似度、RRF 分和重排分。`trace` 还包含各通道 Top K、融合排名、重排前后排名、阶段耗时、模型版本、文档版本和降级原因。前端可以选择四种模式并展开开发者轨迹。

## 消融评测

阶段 3 的 30 条标注保持原文件不变。`stage4_text_queries.json` 通过 `base_dataset` 引用冻结集，再增加 18 条场景语义与空结果查询，共 48 条。新增查询包含通勤降噪、戴眼镜舒适、会议通话、户外运动、游泳防水、长续航和开放式佩戴等。

~~~powershell
npm run eval:text
~~~

产物：

- `evals/reports/stage4-text-ablation.json`
- `evals/reports/stage4-text-ablation.md`

报告保留每种模式的完整逐查询结果、失败 ID、P50/P95 检索耗时、模型与参数。确定性替身下 RRF 优于单路；重排回落到稠密替身的水平，作为真实负结果保留。真实 BGE Provider 的质量与网络延迟仍需在有明确模型服务时独立评测。

## 后续入口

阶段 5 才实现图片向量、商品图片批量编码、以图搜商品和图文混合融合。阶段 5 不得把文本与图片原始相似度直接相加，仍需保留结构化硬过滤、版本身份、独立通道轨迹和可复现消融。
