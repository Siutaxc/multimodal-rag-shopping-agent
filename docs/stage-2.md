# 阶段 2：商品领域模型与确定性数据摄取

## 范围

本阶段只建立可信商品事实、可重跑摄取和结构化读取，不实现全文检索、向量、语义搜索、图片相似度或 Agent。

## 数据模型

| 表 | 核心约束 |
|---|---|
| `products` | 来源身份、幂等键、去重键唯一；金额为 `numeric(12,2)`；时间带时区；缺失事实为 `null` |
| `product_images` | 图片 SHA-256 和商品内位置唯一；只保存对象存储键和元数据 |
| `product_documents` | 商品、文档类型和转换版本唯一；阶段 3 前不建立全文检索列 |
| `review_evidence` | 原始评论身份与主题唯一；评论内容始终视为不可信数据 |
| `ingestion_jobs` | 每次执行记录总数、成功、失败、跳过、错误详情和起止时间 |

迁移文件为 `services/api/migrations/versions/20260722_0001_product_domain.py`。API 容器启动前自动执行迁移；本地可运行 `npm run db:migrate`。

## Fixture 与摄取规则

`data/fixtures/headphones.json` 包含 24 件人工构造耳机，采用 CC0-1.0。它覆盖入耳式、半入耳式、头戴式、贴耳式、骨传导和开放式，包含有线/无线、ANC、价格、续航、重量、颜色、编码和显式缺失值。

摄取规则：

- 拒绝二进制浮点金额，只接受精确字符串或整数；金额最多两位小数。
- 价格必须非负，货币必须在明确白名单内。
- 分钟转换为小时，千克转换为克；未知单位直接报错。
- 中文和英文类别、布尔别名映射为固定枚举；未知值直接报错。
- `source_name + source_id + source_version + transformation_version` 生成幂等键。
- 规范化品牌、标题和品类生成去重键。
- 同一快照重复导入记为跳过；同一来源的新版本更新原商品；缺失字段不推测。
- 每条记录独立失败，不会阻止其他合法记录；最终任务保存错误报告。

## 本地对象存储

`LocalObjectStorage` 以 SHA-256 内容寻址，使用服务端生成的相对键和原子替换，拒绝空文件、不支持的媒体类型和路径穿越。宿主机默认目录为 `data/storage`；Compose 使用 `shoplens-object-storage` 命名卷，实际数据随 Docker WSL 数据根目录保存在 D 盘。

本阶段只负责本地可信 Fixture 文件的存储。远程图片下载、解码校验、元数据清理和上传安全属于阶段 5。

## HTTP API

- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`

列表支持分页、稳定排序，以及 `category`、`brand`、`price_min`、`price_max`、`currency`、`wireless`、`anc`、`battery_hours_min`、`color`、`codec`。所有条件由确定性代码构造参数化查询，接口不接受 SQL。金额响应为十进制字符串。

## 外部 200 条样本状态

没有下载 Amazon Reviews 2023 Electronics 全量文件。官方资料显示该分类约 160 万商品，整个 Hugging Face 数据仓库约 750 GB；当前数据卡未声明数据集许可，而且官方页面给出的部分原始文件链接返回 404。GitHub 仓库的 MIT 许可只明确覆盖代码，不能推定覆盖商品元数据、评论和图片。

因此，200 条外部样本保持待办。继续前需要取得明确的数据使用/再分发许可，并找到支持小范围或流式抽样的有效 HTTPS 来源；下载与解压目录必须位于 D 盘。

- [Amazon Reviews 2023 官方数据说明](https://amazon-reviews-2023.github.io/main.html)
- [McAuley Lab Hugging Face 数据卡](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023)
- [处理代码仓库](https://github.com/hyp1231/AmazonReviews2023)
