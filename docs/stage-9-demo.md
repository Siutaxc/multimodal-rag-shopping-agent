# 阶段 9：四分钟正常与降级演示

## 演示前检查

~~~powershell
npm run stack:fixture
~~~

命令结束时应输出 `result: passed`，并生成 `evals/reports/stage9-fixture-smoke.json`。打开 `http://127.0.0.1:3000`。全程不手工编辑数据库，不依赖付费模型或外部服务。

## 0:00–4:00 正常流程

1. **0:00–0:35，一句话讲架构。** 展示 `docs/diagrams.md`：Next.js 只经 HTTP 调 FastAPI，硬条件由参数化 PostgreSQL 查询保证，pgvector/FTS 做召回，Redis 做会话、缓存与限流，Agent 最多四步且只选择证据 ID。
2. **0:35–1:15，Agent 查询。** 在首页提交“1000 元以内，头戴式，地铁通勤，降噪强，戴眼镜尽量舒服”。指出品类、最高价格、币种、ANC 是硬条件；通勤和舒适是软偏好。结果中的价格和参数来自结构化字段，不来自答案文本。
3. **1:15–1:50，证据深链。** 点击第一件商品的“定位证据”，展示事实/评论锚点、来源 URL、价格时间戳、评论非可信标识与缺失值。回到结果页。
4. **1:50–2:35，图文检索。** 上传 `data/fixtures/images/fixture-001.png`，输入“外观相近的黑色款”，最高价格设为 800。展示图片、文本和融合排名；强调图片只影响排序，预算仍在所有通道前硬过滤。
5. **2:35–3:05，对比。** 加入两件商品，进入对比页，展示统一字段、缺失值与每个单元格的证据链接。
6. **3:05–3:30，轨迹与缓存。** 打开开发者轨迹，指出候选 Top K、RRF、重排、模型/文档版本、工具步骤、引用校验和耗时。再运行 `npm run verify:fixture`，重复搜索必须显示缓存 `HIT`。
7. **3:30–4:00，量化与边界。** 展示阶段 8 图表：150 条 Fixture 上 RRF Recall@10 0.9821、nDCG@10 0.9464；50k 合成行索引后 DB P95 为 0.462/10.681/1.113 ms。同时明确重排和完整多模态融合有保留的负结果，数字不能外推真实模型或生产。

## 4:00–5:00 真实降级演示

启用已提交的故障覆盖。它只把 Reranker 指向容器内不可达的 HTTP 端点，不修改数据库：

~~~powershell
npm run demo:degradation:on
~~~

脚本会真实发起 `mode=rerank` 的 HTTP 查询并断言：结果仍返回、`retrieval_mode=hybrid_rrf_fallback`、trace 含明确降级原因。此时在页面提交文本检索，可展示“部分降级”而商品和硬过滤仍保留。

演示后恢复默认 Fixture：

~~~powershell
npm run demo:degradation:off
npm run verify:fixture
~~~

自动故障注入回归覆盖 Redis fail-open、Provider 重试/熔断、429/`Retry-After`、Prometheus 与浏览器降级提示：

~~~powershell
npm run test:degradation
~~~

## 现场问答的诚实边界

- “这是确定性 Fixture 的可复现工程基线，不是真实 BGE/SigLIP2/LLM 质量。”
- “数据库 P95 不是端到端延迟，也不是并发 SLO。”
- “缓存、限流和指标目前按单 API 进程设计；多副本前有明确改造项。”
- “200 件外部数据因许可证不清晰而延期，没有伪造完成。”
