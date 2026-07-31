# 阶段 9 验收记录

验收日期：2026-07-23  
环境：Windows 11 25H2、Python 3.13.7、Node 22、npm 10、Docker Engine 29.6.2、PostgreSQL 16/pgvector、Redis 7.4  
传输：本地与 Provider 契约均为 HTTP/HTTPS；未使用 WebSocket

## 总控验收矩阵

| 阶段 9 验收项 | 结果 | 证据 |
|---|---|---|
| 新环境按 README 启动 Fixture | 通过 | 独立项目/新命名卷首次导入 24/24，文本和图片索引各 24/24；`stage9-production-smoke.json` passed |
| 演示不手改数据库 | 通过 | 一键 bootstrap；故障覆盖仅切换 HTTP Reranker，输出 `database_changed=false` |
| 关键接口有请求与响应 | 通过 | `docs/api.md`；OpenAPI `/openapi.json` 与 `/docs` |
| 所有指标可从脚本复现 | 通过 | `eval:*`、`perf:stage8`、`verify:fixture` 命令集中于 `docs/evaluation.md` |
| 简历每个数字可回链 | 通过 | `docs/evaluation.md` 溯源表和 `docs/resume-and-interview.md` |

## 静态、单元与构建

最终 `npm run check`：

- Ruff：通过；
- mypy strict：98 个源文件无问题；
- 后端：收集 185，排除 2 个 integration，183/183 通过；
- ESLint：0 warning；
- TypeScript strict：通过；
- Vitest：5 个文件、9/9 通过；
- Next.js 16.2.10 生产构建：通过，`/`、`/results`、`/compare`、`/products/[id]`、`/traces/[id]` 路由生成成功。

保留一个现有测试依赖警告：Starlette `TestClient` 提示未来迁移 `httpx2`。它不影响本轮结果，但升级 FastAPI/Starlette 测试栈时应处理。

## PostgreSQL/Redis 集成

阶段 9 将 Compose 宿主端口收紧到 `127.0.0.1` 后，首次分拆集成测试发现后端默认 DSN 仍为 `localhost`；当前 Windows 优先解析到 `::1`，导致 readiness 报 PostgreSQL/Redis unavailable。修复为默认 `127.0.0.1`，并新增单元测试锁定 DSN 与 Compose 绑定一致。

修复后分别运行：

- `test_infrastructure.py`：1/1，通过，真实 PostgreSQL、pgvector、Redis 就绪；
- `test_stage2_product_data.py::test_product_data_and_lexical_search_from_empty_database_through_http`：1/1，通过，9.65 秒。

后者从临时空库执行 `0001 → 0005`、`alembic check`、24 件摄取、keyset 文本/图片向量回填、阶段 3～5 评测，以及商品、文本、图片、图文、Agent、会话、轨迹和对比 HTTP。临时数据库在 `finally` 删除，主库未修改。

## 一键 Fixture 与 HTTP 烟测

`npm run stack:fixture` 最终退出码 0：

- 四个服务全部 `healthy`；
- 主卷已有 24 件商品，本轮幂等导入结果 `skipped=24`；
- 文本与图片向量各 `skipped=24`，版本身份保持不变；
- readiness=`ready`，Fixture 商品 24；
- RRF 查询返回 2 件且全部满足 over-ear、CNY 1000、ANC 硬条件；
- 重复查询 `X-ShopLens-Cache=HIT`；
- Agent `completed`，2 个结构化推荐、30 条证据、2 个工具步骤、引用校验通过；
- `/metrics`、Web 首页和 `/og.png` 均返回 200。

固定基础镜像摘要后再次执行基础/生产 Compose `config --quiet`、`up -d --build --wait` 与 `npm run verify:fixture`，结果仍为 passed。主报告：`evals/reports/stage9-fixture-smoke.json`。

## 真正的全新环境

使用独立项目名 `shoplens-stage9-production-smoke`、全新网络/命名卷和备用 HTTP 端口 13001/18001 启动基础 Compose + production overlay：

- PostgreSQL、Redis、API、Web 全部 healthy；
- production 模式下 API/Web 的只读根文件系统、非 root、capabilities 删除和资源/日志策略可启动；
- 首次导入 `succeeded=24, skipped=0, failed=0`；
- 首次文本向量 `indexed=24`，图片向量 `indexed=24`；
- 完整 HTTP 烟测 passed，报告为 `evals/reports/stage9-production-smoke.json`。

验收后只删除该专用项目的容器、网络、三个命名卷和两个本地构建镜像；这些数据是本轮合成副本且不可恢复。主 `shoplens` 项目及命名卷未触碰。

## 浏览器与降级

- Playwright 确定性桌面/移动：10/10 通过；默认跳过 2 个 live 用例；
- 真实 Compose HTTP 桌面/移动：2/2 通过；
- `npm run test:degradation`：后端故障注入 7/7，Reranker 降级 UI 桌面/移动 2/2；
- 真实故障档位：不可达 HTTP Reranker 产生 `hybrid_rrf_fallback`、`reranker_error`，仍返回 2 件硬条件合规商品；随后 `demo:degradation:off` 恢复 Fixture 并复验 passed。

## 部署配置

- Python/Node/pgvector/Redis 基础镜像固定至本轮实际验收的 manifest SHA-256；
- PostgreSQL/Redis 不在 production overlay 暴露宿主端口；
- API/Web 默认只监听宿主 `127.0.0.1`，公网入口必须由 HTTPS 反向代理提供；
- CORS 使用 JSON 环境变量显式配置 HTTP/HTTPS origin；
- 开发 trace 在 production 固定 404；
- 根文件系统只读，图片对象写入专用卷，`/tmp` 使用受限 tmpfs。

## 未关闭但不阻塞阶段 9 的边界

- 真实 BGE-M3、BGE Reranker、SigLIP2 与 Agent HTTPS 端点仍未实测；Fixture 指标不能外推；
- 200 件外部商品因数据许可证不明确继续延期；
- 多 worker/multi-replica 前需要 multiprocess 指标、共享熔断语义、认证授权和共享对象存储；
- 本轮容器 `npm ci` 汇总报告构建依赖图有 1 moderate、2 high；未运行 `npm audit fix --force`，需要按 advisory 定向升级并重新验收；
- Dockerfile 的基础镜像已固定，但 Python 依赖仍是版本范围而非 hash lock；进一步供应链加固可生成受审依赖锁和 SBOM。

## 结论

阶段 9 六项任务和五项验收全部完成。阶段 1～9 至此闭环；项目没有定义自动开始的阶段 10，后续仅在用户明确要求时处理真实数据/模型、认证、多副本或漏洞定向升级。
