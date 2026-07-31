# 阶段 5：多模态检索

## 范围

阶段 5 在不修改阶段 3/4 文本基线的前提下，增加版本化商品图片向量、安全图片上传、纯图片召回、图文排名融合、显式降级、离线消融和前端上传体验。本阶段不包含自然语言条件解析、Agent、会话追问和商品对比生成。

默认图片 Provider 是确定性像素特征替身，只用于离线 CI 与工程链路验证，不能代表真实 SigLIP2 效果。真实 Provider 通过 HTTP/HTTPS JSON 端点接入，不使用 WebSocket。

## 数据与版本隔离

Alembic `20260722_0004` 新增：

- `image_embeddings`：每条记录绑定 `product_images.id`、模型名、模型版本、固定 768 维、表示版本、源图片 SHA-256、状态、生成时间和失败原因。
- `uploaded_image_assets`：仅记录清洗后对象的存储键、原始/清洗后哈希、媒体类型、字节数和尺寸；客户端只能使用不透明 `asset_id`。
- `ix_image_embeddings_hnsw_cosine`：只索引 `status = 'ready'` 的 `vector_cosine_ops` HNSW。

查询必须完整匹配模型名、模型版本、维度和 `stage5-product-image-v1` 表示版本。切换模型会生成并存的新记录，不会读取旧向量。图片原始相似度不与文本相似度相加。

24 件 CC0 Fixture 各有一张由脚本生成的可复现 PNG 插画。`generate_stage5_images.py` 的产物只用于测试和演示；导入服务可为阶段 4 已存在但没有图片的商品安全回填图片，而不会重建文本文档或文本向量。

## 安全上传

`POST /api/v1/assets/images` 直接接收单张图片的原始 HTTP 请求体，支持 JPEG、PNG 和 WebP。服务执行：

1. 在流式读取时限制 `Content-Length` 和实际累计字节数，默认上限 5 MiB。
2. 拒绝声明类型与解码格式不一致、无法解码、截断、动画和不支持的格式。
3. 限制像素总量与单边尺寸，默认分别为 2000 万像素和 4096 像素。
4. 应用 EXIF 方向后转换为 RGB，再编码为无损 WebP；不保留原始文件或不必要元数据。
5. 通过 SHA-256 内容寻址原子写入对象存储，并返回数据库 `asset_id`。

SVG 不进入不可信上传链路。价格、ANC、品类、颜色等硬条件不会从图片推断，只能来自请求中的白名单字段和数据库事实。

## Provider 与索引

`ImageEmbeddingProvider` 提供 `identity` 和批量 `embed_images` 契约：

- `DeterministicImageEmbeddingProvider`：固定 768 维像素网格、颜色直方图和边缘特征，保证可复现 CI；不冒充 SigLIP2。
- `Siglip2HttpImageEmbeddingProvider`：只接受 HTTP/HTTPS 端点，以有界 JSON 请求发送 Base64 图片，校验数量、维度、有限数值、超时和错误响应。
- `ImageEmbeddingIndexer`：按批次创建 `pending` 记录，成功置为 `ready`；内容哈希未变时跳过，失败记录可重试，模型版本切换时并存。

索引命令：

~~~powershell
npm run data:index:image
~~~

## 检索与降级

`POST /api/v1/multimodal-search` 接收 `asset_id`、可选文字 `query` 和与文本搜索相同的结构化 `filters`：

- 无文字：只运行图片向量召回，返回 `pgvector_image`。
- 有文字：运行阶段 4 文本链路和图片链路，再按通道排名执行带权 RRF，返回 `multimodal_rrf`。
- 图片 Provider 超时/错误/活动索引为空且有文字：保留文本结果，返回 `multimodal_text_fallback` 和原因。
- 纯图片查询遇到图片故障：返回 `image_unavailable`，不伪造文本查询。

所有通道使用同一组参数化硬过滤。响应分别保留 `image_score`、文本通道分数、通道排名和 `fusion_score`，开发轨迹记录模型、参数、资产哈希、候选、融合和耗时。

融合公式只使用排名：

~~~text
score(d) = text_weight / (rrf_k + text_rank)
         + image_weight / (rrf_k + image_rank)
~~~

默认 `text_weight = 1.0`、`image_weight = 1.25`、`rrf_k = 60`。这些参数必须通过评测报告解释，不能把不同模型的原始相似度直接相加。

## 评测与边界

`stage5_multimodal_queries.json` 包含 12 条纯图片和 12 条图文查询，并保留两个合理空结果。报告比较：

- `pure_image`
- `mixed_image_only`
- `mixed_text_only`（去掉图片通道）
- `mixed_full`

运行：

~~~powershell
npm run eval:multimodal
~~~

报告输出到 `evals/reports/stage5-multimodal-ablation.{json,md}`。当前 Fixture 上完整融合的 nDCG@10 低于文本消融，负结果已如实保留；原因包括合成图过于规则、查询文字通常已能明确目标、固定图片权重尚未在更大真实图像集上校准。
