# 架构与评测图表

这些图只使用已提交的架构和冻结报告数据。详细解释分别见 `docs/architecture.md` 与 `docs/evaluation.md`。

## 端到端组件关系

~~~mermaid
flowchart TB
    subgraph Client["Client"]
      W["Next.js Web"]
    end
    subgraph API["FastAPI process"]
      O["HTTP middleware\nrequest ID / rate / metrics"]
      A["Bounded Agent"]
      S["Text + multimodal retrieval"]
      E["Evidence + citation validator"]
    end
    subgraph State["State and retrieval"]
      P[("PostgreSQL FTS")]
      V[("pgvector HNSW")]
      R[("Redis cache / session / trace")]
      F[("Image volume")]
    end
    subgraph Providers["Replaceable providers"]
      H["HTTP/HTTPS adapters"]
      D["Offline deterministic fixtures"]
    end
    W -->|"HTTP"| O
    O --> A
    O --> S
    A --> S
    A --> E
    S --> P
    S --> V
    S --> R
    A --> R
    O --> F
    S --> H
    S --> D
    A --> H
    A --> D
~~~

## 事实与证据流

~~~mermaid
flowchart LR
    U["Untrusted user / review / image"] --> C["Schema + image sanitization"]
    C --> Q["Parameterized retrieval"]
    T["Validated product facts"] --> Q
    Q --> B["Evidence bundle with stable IDs"]
    B --> M["Model may select known evidence IDs"]
    M --> V["Cross-product / field citation validation"]
    V --> R["Deterministic facts, comparison cells and answer"]
    R --> F["Frontend renders structured fields"]
~~~

## 150 条文本消融

~~~mermaid
xychart-beta
    title "Stage 8 Fixture retrieval quality"
    x-axis ["Lexical", "Dense", "RRF", "Rerank"]
    y-axis "score" 0.5 --> 1.0
    line "Recall@10" [0.5923, 0.9772, 0.9821, 0.9772]
    line "nDCG@10" [0.5923, 0.9072, 0.9464, 0.9072]
~~~

RRF 在当前 Fixture 上胜出；重排没有提升，不能把真实 BGE Reranker 的名字附到这些数字上。

## 50k 数据库查询 P95

~~~mermaid
xychart-beta
    title "50k synthetic rows: P95 before vs after indexes"
    x-axis ["Hard filter", "FTS", "ANN"]
    y-axis "milliseconds" 0 --> 250
    bar "Before" [23.389, 39.634, 239.207]
    bar "After" [0.462, 10.681, 1.113]
~~~

这里是单机、暖机、20 次采样的数据库查询时间，不是端到端 API SLO。完整执行计划与索引构建成本在 `evals/reports/stage8-performance.json`。
