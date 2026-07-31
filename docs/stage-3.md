# 阶段 3：PostgreSQL 词法检索基线

日期：2026-07-22  
范围：纯文本词法召回、确定性硬过滤、离线评测和最小前端闭环

## 范围与边界

阶段 3 只实现 PostgreSQL 全文检索，不包含 Embedding、向量召回、HNSW、RRF、Reranker、LLM 条件解析或 Agent。所有浏览器与 API 通信继续使用 HTTP/HTTPS，没有增加 WebSocket。

当前语料仍是 `data/fixtures/headphones.json` 中 24 件 CC0 人工商品。外部 200 条样本因数据许可未明确继续延期；这不阻塞工程基线，但本阶段指标不能解释为生产效果。

## 数据库与词法文档

Alembic 迁移 `20260722_0002` 在 `product_documents` 增加：

- `search_text`：事实限定、可回填的检索文本；
- `search_vector`：由 PostgreSQL `to_tsvector('simple', search_text)` 生成的存储列；
- `ix_product_documents_search_vector_gin`：GIN 索引。

迁移会从阶段 2 的 `products` 和 `product_documents` 原位回填，不删除商品、来源文档或摄取记录。空库执行 `0001 → 0002` 与阶段 2 主库执行 `0001 → 0002` 均已验证。

检索文档版本为 `stage3-lexical-v1`，构造代码位于 `services/api/app/retrieval/documents.py`。文档只包含已有事实：

- 品牌、完整标题、型号和标准品类；
- 可审查的中英文品类别名；
- 价格、币种、无线、ANC、续航、重量、颜色、编码、防水和麦克风；
- 商品描述中确实出现的有限场景词，例如“通勤”“办公”“户外”“运动”。

缺失值不会被补猜。PostgreSQL `simple` 配置不提供通用中文分词，因此这里只暴露明确别名和原文中已出现的场景词；该限制保留给阶段 4 的稠密召回做真实对照。

## 搜索 API

`POST /api/v1/search` 接受查询文本、分页和白名单硬过滤：

~~~json
{
  "query": "Auralis Metro ANC 40",
  "page": 1,
  "page_size": 12,
  "filters": {
    "category": "over_ear",
    "price_max": "1000.00",
    "currency": "CNY",
    "anc": true
  }
}
~~~

过滤字段覆盖品类、品牌、价格区间、币种、无线、ANC、最低续航、颜色和编码。未知字段、空查询和反向价格区间返回 422。SQLAlchemy 只生成绑定参数，不接受 SQL、数据库字段名或排序表达式。

响应明确包含：

- `retrieval_mode: postgresql_lexical`；
- `search_document_version: stage3-lexical-v1`；
- 每条商品的 `rank`、`lexical_score` 和来源文档版本；
- 实际应用的硬过滤、分页与总数。

排序由 PostgreSQL `ts_rank_cd`、完整标题包含加分和品牌精确匹配加分组成；同分时按标题和商品 UUID 稳定排序。

## 评测

评测集位于 `evals/datasets/stage3_lexical_queries.json`，共 30 条，相关性标注使用稳定的 `source_id`，不依赖每次导入变化的数据库 UUID。覆盖：

- 12 条精确品牌/型号；
- 品牌、ANC、品类、有线/无线与中文场景词；
- 价格、品类、ANC、编码、颜色、续航等组合硬过滤；
- 1 条预期空结果。

执行命令：

~~~powershell
npm run eval:lexical
~~~

产物：

- `evals/reports/stage3-lexical-baseline.json`
- `evals/reports/stage3-lexical-baseline.md`

指标包括 Recall@5、Recall@10、Precision@5、nDCG@10、MRR、硬条件违反率和空结果准确率。报告保留全部查询的预期与实际 `source_id`，不会隐藏失败案例。

## 前端

`http://localhost:3000` 现在提供查询词、品类、最高价格和 ANC 过滤器，调用 HTTP `POST /api/v1/search`，显示排名、词法分、结构化事实和详情链接。动态详情页调用 `GET /api/v1/products/{product_id}`，展示价格观测时间、参数、数据来源与原始 HTTPS URL。

## 后续入口

阶段 4 开始前应保留本阶段报告作为不可改写的词法对照。阶段 4 再实现版本化文本向量、稠密召回、RRF、重排、消融实验和超时降级；不得为了制造提升而修改本阶段标注。
