# 阶段 9：部署、文档与面试交付

## 结论

阶段 9 已在 2026-07-23 闭环。ShopLens 现在既可以由新使用者一条命令启动 Fixture 模式，也有明确的架构、数据、HTTP API、评测、已知限制、演示和面试材料。阶段 3～8 的冻结数据集与报告没有被改写。

## 可运行交付

- `npm run stack:fixture` 在容器内完成构建、健康等待、Alembic 迁移、24 件 Fixture 幂等导入、文本/图片向量回填和 HTTP 烟测；宿主机不需要 Python 环境。
- `npm run verify:fixture` 独立验证 readiness、24 件来源商品、硬过滤、Redis 缓存 HIT、有界 Agent、证据、引用校验、Prometheus、Web 和 OG 图片，并输出 JSON 报告。
- 基础 Compose 的 PostgreSQL、Redis、API 和 Web 只绑定 `127.0.0.1`；本机默认 DSN 同步使用 IPv4 回环，避免 Windows `localhost → ::1` 与绑定地址不一致。
- Python、Node、pgvector、Redis 基础镜像使用可读标签加 manifest SHA-256 固定构建输入。
- `infra/docker-compose.production.yml` 隐藏 PostgreSQL/Redis 宿主端口，对 API/Web 使用非 root、只读根文件系统、删除 capabilities、`no-new-privileges`、日志轮转、退出宽限期和资源上限。
- CORS 来源改为环境可配置的 HTTP/HTTPS 列表；生产模板要求显式替换域名与密钥。
- CI 的 infrastructure 作业从空环境启动全栈、导入/索引并上传阶段 9 烟测 JSON。

## 可降级演示

`infra/docker-compose.degradation.yml` 只把 Reranker 指向容器内不可达的 HTTP 端点，并切换独立缓存命名空间。`npm run demo:degradation:on` 会实际断言 `hybrid_rrf_fallback` 和机器可读降级原因；`npm run demo:degradation:off` 恢复默认 Fixture。两条命令不改数据库。

`npm run test:degradation` 聚合 Redis fail-open、Provider 重试/熔断、429、指标和桌面/移动浏览器降级提示。

## 文档交付

| 材料 | 文件 |
|---|---|
| 从零启动、单机生产覆盖与运维边界 | `docs/deployment.md` |
| 组件、检索、Agent、证据与信任边界 | `docs/architecture.md` |
| 来源、实体、版本、图片安全与冻结规则 | `docs/data.md` |
| 关键接口请求/响应、错误和缓存头 | `docs/api.md` |
| 复现命令、指标、性能与数字溯源 | `docs/evaluation.md` |
| 架构、证据流、消融和性能图表 | `docs/diagrams.md` |
| 数据、模型、安全、一致性和部署限制 | `docs/known-limitations.md` |
| 四分钟正常流程和一分钟真实降级 | `docs/stage-9-demo.md` |
| 简历三条、三个 STAR 与高频取舍问答 | `docs/resume-and-interview.md` |

## 关键取舍

- 作品交付优先保证确定性和可复现，因此默认继续使用离线 Fixture Provider；真实 BGE/SigLIP2/Agent 质量仍未宣称。
- 生产覆盖是单机安全基线，不伪装成多副本高可用。多 worker 指标、共享熔断、认证授权、共享对象存储、备份和并发 SLO 都列为明确边界。
- 外部 200 件商品继续因数据许可证不明确而延期；没有为展示规模伪造来源。
- Reranker 与完整图文融合的负结果继续保留。简历数字必须带 Fixture/合成/DB 查询限定并回链冻结报告。

## 验收入口

本阶段的命令、实测数量、干净环境结果和剩余警告见 `docs/stage-9-validation.md`。主环境报告为 `evals/reports/stage9-fixture-smoke.json`；独立全新生产覆盖环境报告为 `evals/reports/stage9-production-smoke.json`。
