# 数据、版本与来源

## 可复现数据集

默认语料是 `data/fixtures/headphones.json` 中 24 件人工合成耳机，以及 `data/fixtures/images/` 中对应的 CC0 合成图片。`source_name=shoplens_deterministic_fixture`，每件商品有稳定 `source_id`、HTTPS 来源占位 URL、来源版本、转换版本和价格观察时间。数据用于工程回归，不宣称是真实电商库存、真实评论或实时价格。

原计划首批 200 件外部商品未导入。Amazon Reviews 2023 的数据卡没有给出足以覆盖商品、评论与图片再分发的明确许可证；代码仓库的 MIT 许可证不能推定为数据许可证。因此项目保留延期结论，没有下载全量数据、伪造来源或把外部数据包装成已完成。

## 核心实体

| 实体 | 关键内容 | 审计身份 |
|---|---|---|
| `products` | 标题、品牌、品类、精确金额、币种、ANC、续航、重量等 | `source_id + source_version + transformation_version` |
| `product_images` | 原图来源、内容哈希、媒体类型、尺寸、存储键 | SHA-256 内容寻址 |
| `review_evidence` | 主题、短摘录、评分、来源和日期 | 来源 review ID；始终标记为非可信内容 |
| `product_documents` | 只包含允许检索的事实文本和 `tsvector` | 文档版本 + 内容哈希 |
| `text_embeddings` | 1024 维向量、状态、模型/版本、文档版本 | 完整版本身份 + 源哈希 |
| `image_embeddings` | 768 维向量、状态、模型/版本、表示版本 | 完整版本身份 + 图片哈希 |
| `uploaded_image_assets` | 净化后的 WebP、尺寸、哈希和不透明 ID | 内容哈希 + 随机 UUID |
| `ingestion_jobs` | 总数、成功、失败、跳过与逐项错误 | 每次摄取运行记录 |

金额在 PostgreSQL 使用 `numeric(12,2)`，HTTP JSON 使用十进制字符串，避免二进制浮点误差。时间统一归一化为 UTC；单位、枚举、颜色和编码由严格 Schema 归一化。缺失事实保持 `null`，不会用描述、评论或模型猜测填充。

## 摄取和版本生命周期

~~~mermaid
flowchart LR
    S["licensed source or CC0 fixture"] --> V["strict schema validation"]
    V --> N["currency / time / unit normalization"]
    N --> U["source-key idempotent upsert"]
    U --> D["versioned search document"]
    D --> T["keyset text embedding batches"]
    U --> I["sanitize + content-address images"]
    I --> E["keyset image embedding batches"]
    T --> Q["ready vectors selected by full version identity"]
    E --> Q
~~~

导入以来源身份幂等：未变化记录计为 `skipped`，变化记录更新并保留运行统计。向量回填按 UUID keyset 分页，每批单独提交并记录失败；内存受批大小约束。新模型版本与旧版本并存，查询必须同时匹配模型名、模型版本、维度、文档/表示版本和 ready 状态，禁止混用向量空间。

## 图片安全

上传接口接收 JPEG/PNG/WebP 原始字节，不接收任意文件路径。处理顺序是请求体字节上限、MIME/解码校验、动画拒绝、像素与边长上限、应用 EXIF 方向、无损 WebP 重编码和元数据清除。对象存储按净化后内容的 SHA-256 寻址；外部只返回不透明 `asset_id`，不暴露本地路径。

## 评测数据冻结规则

- 阶段 3 的 30 条词法查询和阶段 4 的 18 条语义查询是冻结基线；阶段 8 只新增 102 条，没有改写早期标签。
- 阶段 5 保留 12 条纯图片和 12 条图文查询；完整融合不如文字消融的负结果没有删除。
- 阶段 6 保留 15 个多轮场景与 384 条结构化事实声明。
- 阶段 8 的 5k/50k 行是从 24 件 Fixture 合成复制的规模数据，只验证执行路径与索引，不代表真实分布。

详细指标和复现命令见 `docs/evaluation.md`。
