# 系统架构

## 总览

ShopLens 把“模型擅长的语义理解”和“代码必须保证的事实约束”分开。浏览器只消费结构化响应；预算、品类、币种、ANC 等硬条件由白名单 Schema 和参数化 SQL 保证；模型只能解析受限 Schema 或选择证据 ID，不能生成 SQL、决定工具循环或直接写价格事实。

~~~mermaid
flowchart LR
    U["Browser / Next.js"] -->|"HTTP JSON"| A["FastAPI"]
    A --> R["Rate limit + request metrics"]
    R --> G["Bounded Agent state machine\nmax 4 tool steps"]
    R --> S["Text / multimodal search"]
    G --> S
    G --> E["Evidence builder + citation validator"]
    S --> F["Whitelist hard filters"]
    F --> P[("PostgreSQL 16\nproducts + FTS")]
    S --> V[("pgvector\ntext/image HNSW")]
    S --> C[("Redis\ncache")]
    G --> C2[("Redis\nsessions + traces")]
    S --> H["HTTP/HTTPS model adapters\nor offline fixtures"]
    A --> O["Content-addressed image volume"]
    A --> M["JSON logs + /metrics"]
~~~

## 检索路径

文本请求先转换为明确的 `SearchFiltersInput`，再用相同硬过滤分别执行 PostgreSQL FTS 和文本向量召回。RRF 只融合通道内排名；可选 Reranker 只处理有限 Top K，失败时保留 RRF 顺序。图文请求先净化上传图片并生成图片向量，再把图片排名与文本排名做带权 RRF；图片模型不判断价格、ANC 或品类。

~~~mermaid
flowchart TD
    Q["query + optional image + filters"] --> W["Pydantic whitelist validation"]
    W --> F["parameterized hard-filter predicate"]
    F --> L["PostgreSQL FTS Top K"]
    F --> D["text pgvector Top K"]
    F --> I["image pgvector Top K"]
    L --> R["rank-only RRF"]
    D --> R
    I --> R
    R --> K["bounded rerank Top K"]
    K -->|"success"| X["structured results + trace"]
    K -->|"timeout/error"| Y["RRF fallback + degraded reason"]
~~~

## Agent 与证据链

Agent 是代码固定的状态机，不是开放式 ReAct。一次请求最多四步，当前实测最多三步：读取会话、检索、批量详情或对比。商品事实、评论摘录和缺失值先形成证据包；模型计划最多选择产品和证据 ID，最终文本、价格、参数、对比单元格由确定性渲染器生成。引用校验拒绝未知证据、跨商品证据和字段不一致证据。

~~~mermaid
sequenceDiagram
    participant B as Browser
    participant A as Bounded Agent
    participant T as Approved tools
    participant D as PostgreSQL/pgvector
    participant R as Redis
    B->>A: HTTP assistant query
    A->>R: read opaque session context
    A->>A: parse strict intent/filter schema
    A->>T: search_catalog
    T->>D: parameterized filters + ranked retrieval
    D-->>T: structured candidates
    A->>T: get_product_detail / compare_products
    T->>D: facts + review evidence
    A->>A: evidence-ID plan + citation validation
    A->>R: store session and development trace
    A-->>B: structured recommendations + evidence + trace ID
~~~

## 信任边界

| 输入/组件 | 信任级别 | 允许影响 | 不允许影响 |
|---|---|---|---|
| 结构化商品字段 | 经过摄取校验的事实 | 硬过滤、价格/参数展示、证据 | 绕过来源与时间戳 |
| 商品描述、评论、图片文字 | 非可信内容 | 召回特征、带来源的摘录 | 工具选择、SQL、系统指令、硬条件 |
| 用户文本 | 非可信输入 | 受限意图、软偏好、白名单条件 | 原始 SQL、任意工具、无限循环 |
| 远程模型 | 非可信建议者 | 返回严格 Schema、选择已知证据 ID | 直接生成事实、执行 SQL、放宽硬条件 |
| 前端 | 展示层 | 读取结构化商品和证据 | 从自然语言答案反向解析事实 |

## 韧性与可观测性

搜索缓存与限流使用 Redis；Redis 故障时 fail-open，核心检索仍可用。四类远程 Provider 共享超时、最多三次重试和 closed/open/half-open 熔断；每条降级路径都返回机器可读原因。请求日志不记录查询、会话、参数或密钥；路径 UUID 会归一化，数据库只记录语句类型、耗时和哈希指纹，避免高基数与敏感内容泄漏。
