# HTTP API 示例

默认基址为 `http://127.0.0.1:8000`。完整机器可读契约见 `GET /openapi.json`，交互文档见 `GET /docs`。以下响应为字段裁剪后的代表性示例；UUID 和耗时每次运行都会变化。

## 就绪探针

~~~powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/ready
~~~

~~~json
{
  "status": "ready",
  "checks": {"postgresql": "ok", "pgvector": "ok", "redis": "ok"}
}
~~~

`/health/live` 只检查进程；`/health/ready` 检查 PostgreSQL、vector 扩展与 Redis，依赖不可用时返回 503。

## 商品列表和详情

~~~powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/products?category=over_ear&price_max=1000&currency=CNY&anc=true&page_size=3'
~~~

~~~json
{
  "items": [{
    "id": "<product_uuid>",
    "title": "Auralis Metro ANC 40",
    "brand": "Auralis",
    "category": "over_ear",
    "price_amount": "899.00",
    "currency": "CNY",
    "anc": true,
    "source_name": "shoplens_deterministic_fixture",
    "source_url": "https://fixtures.shoplens.local/products/fixture-001"
  }],
  "page": 1,
  "page_size": 3,
  "total": 2
}
~~~

`GET /api/v1/products/{product_id}` 额外返回描述、规格、图片、评论证据、来源版本和创建/更新时间。未知 ID 返回 404；`price_min > price_max` 返回 422。

## 文本检索

~~~powershell
$body = @{
  query = '地铁通勤降噪头戴式'
  mode = 'rrf'
  page_size = 3
  filters = @{category='over_ear'; price_max=1000; currency='CNY'; anc=$true}
} | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/v1/search `
  -Method Post -ContentType 'application/json' -Body $body
~~~

~~~json
{
  "retrieval_mode": "hybrid_rrf",
  "search_document_version": "stage3-lexical-v1",
  "dense_document_version": "stage4-dense-v1",
  "query": "地铁通勤降噪头戴式",
  "applied_filters": {"category":"over_ear","price_max":"1000","currency":"CNY","anc":true},
  "items": [{
    "rank": 1,
    "dense_rank": 1,
    "rrf_score": 0.0163934426,
    "document_version": "stage4-dense-v1",
    "product": {"id":"<product_uuid>","title":"Auralis Metro ANC 40","price_amount":"899.00","currency":"CNY","anc":true}
  }],
  "page": 1,
  "page_size": 3,
  "total": 2,
  "trace": {
    "parameters":{"lexical_candidate_k":50,"dense_candidate_k":50,"fusion_candidate_k":30,"rrf_k":60},
    "models":{"embedding":"BAAI/bge-m3@fixture-semantic-v1:1024","dense_document":"stage4-dense-v1"},
    "degraded_reason":null,
    "channels":{"lexical":[],"dense":[]},
    "fusion":[],
    "rerank":[],
    "latency_ms":{"lexical":21.689,"dense":13.898,"fusion":0.205,"total":35.887}
  }
}
~~~

`mode` 可选 `lexical`、`dense`、`rrf`、`rerank`。响应头 `X-ShopLens-Cache` 为 `MISS` 或 `HIT`；Reranker 失败时 `retrieval_mode` 和 trace 显示 RRF 降级。硬条件在每个召回通道之前应用。

## 图片上传和图文检索

图片作为原始请求体发送，不使用 multipart：

~~~powershell
$upload = Invoke-RestMethod http://127.0.0.1:8000/api/v1/assets/images `
  -Method Post -ContentType 'image/png' `
  -InFile data/fixtures/images/fixture-001.png
$upload
~~~

~~~json
{
  "asset_id": "<asset_uuid>",
  "media_type": "image/webp",
  "byte_size": 3492,
  "width": 512,
  "height": 512,
  "content_sha256": "<sha256>"
}
~~~

~~~powershell
$body = @{
  asset_id = $upload.asset_id
  query = '外观相近的黑色头戴式，预算 800 元'
  filters = @{category='over_ear'; price_max=800; currency='CNY'}
} | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/v1/multimodal-search `
  -Method Post -ContentType 'application/json' -Body $body
~~~

响应包含 `retrieval_mode`、`image_rank/image_score`、文本通道排名、`fusion_score`、结构化商品和完整 trace。未知 `asset_id` 返回 404；无效、超限或动画图片返回 413/422。

## 有界 Agent

~~~powershell
$body = @{
  message = '预算 1000 元以内，地铁通勤用的降噪头戴式耳机'
  filters = @{category='over_ear'; price_max=1000; currency='CNY'; anc=$true}
} | ConvertTo-Json -Depth 5
$answer = Invoke-RestMethod http://127.0.0.1:8000/api/v1/assistant/query `
  -Method Post -ContentType 'application/json' -Body $body
$answer
~~~

~~~json
{
  "status": "completed",
  "session_id": "<session_uuid>",
  "answer": "找到 2 件满足当前硬条件的候选，价格和参数均来自带来源的商品记录。",
  "recommendations": [{
    "rank": 1,
    "product": {"id":"<product_uuid>","title":"Auralis Metro ANC 40","price_amount":"899.00","anc":true},
    "matched_requirements": [{"text":"类型为 over_ear","evidence_ids":["<evidence_id>"]}],
    "reasons": [],
    "tradeoffs": [],
    "evidence_ids": ["<evidence_id>"]
  }],
  "applied_filters": {"category":"over_ear","price_max":"1000","currency":"CNY","anc":true},
  "evidence": [{"id":"<evidence_id>","kind":"product_fact","field":"title","value":"Auralis Metro ANC 40","source_name":"shoplens_deterministic_fixture"}],
  "trace_id": "<trace_uuid>",
  "trace": {"states":["ParseRequest","SearchCatalog","GetProductDetail","ComposeAnswer","ValidateCitations"],"tool_steps":[{"step":1,"tool":"search_catalog","status":"ok"},{"step":2,"tool":"get_product_detail","status":"ok"}],"citation_validation":{"valid":true,"errors":[]},"degraded_reasons":[]},
  "warnings": []
}
~~~

后续轮次把 `session_id` 原样放回请求即可继承条件；`clear_fields` 可清除指定条件。响应的商品、事实和引用均来自结构化字段，前端不解析 `answer` 提取事实。

## 商品对比、会话和轨迹

~~~powershell
$body = @{product_ids=@('<product_uuid_1>','<product_uuid_2>')} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/v1/products/compare `
  -Method Post -ContentType 'application/json' -Body $body
~~~

对比响应复用 `AssistantResponse`，并增加 `comparison.product_ids` 与逐字段 `rows[].values[].evidence_id`。只允许 2～4 个唯一 UUID。

~~~powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/sessions/<session_uuid>
Invoke-RestMethod http://127.0.0.1:8000/api/v1/traces/<trace_uuid>
~~~

轨迹端点只在非生产环境开放；生产环境固定返回 404。会话和轨迹使用不透明 UUID，并受 Redis TTL 约束。

## 指标和通用错误

~~~powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/metrics
~~~

Prometheus 文本包含 HTTP、数据库、缓存、限流和 Provider 指标。昂贵 POST 默认每客户端每 60 秒 120 次；超限返回 429 与 `Retry-After`。所有 422 响应遵循 FastAPI/Pydantic 的结构化校验错误格式；请求可携带 `X-Request-ID`，非法值会被替换为安全 UUID。
