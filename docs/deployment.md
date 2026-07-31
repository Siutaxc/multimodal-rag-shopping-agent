# 部署与 Fixture 启动

## 一条命令得到可演示环境

前提是 Docker Desktop 已启动；通过 `npm` 调用时还需要 Node.js 20.9+ 与 npm 10+。默认配置只监听本机回环地址，所有服务调用均使用 HTTP。

~~~powershell
npm run stack:fixture
~~~

不想安装 Node.js 时，可直接运行同一脚本：

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap-fixture.ps1
~~~

脚本会按固定顺序执行：

1. 构建并在后台启动 PostgreSQL/pgvector、Redis、FastAPI 和 Next.js，等待健康检查通过；
2. 在 API 容器中执行 Alembic 迁移；容器入口已经保证迁移先于服务启动；
3. 幂等导入 24 件 CC0 确定性 Fixture；
4. 回填版本化文本向量和图片向量；
5. 通过 HTTP 验证商品数、硬过滤、缓存 HIT、Agent 证据/引用、四步上限、指标、Web 和 OG 图片；
6. 写出 `evals/reports/stage9-fixture-smoke.json`。

重复运行不会生成重复商品。单独复验已运行环境：

~~~powershell
npm run verify:fixture
~~~

入口：Web `http://127.0.0.1:3000`，OpenAPI `http://127.0.0.1:8000/docs`，就绪探针 `http://127.0.0.1:8000/api/v1/health/ready`，Prometheus `http://127.0.0.1:8000/metrics`。

停止容器但保留命名卷：

~~~powershell
npm run stack:down
~~~

该命令不带 `-v`，不会删除 PostgreSQL、Redis 或对象存储卷。

## 配置与持久化

- 开发默认值在 `.env.example`；Compose 中没有写入真实密钥。
- PostgreSQL、Redis、API、Web 的宿主端口默认只绑定 `127.0.0.1`。
- `shoplens-postgres-data`、`shoplens-redis-data`、`shoplens-object-storage` 三个命名卷分别保存关系数据、会话/缓存和净化后的上传图片。
- Fixture Provider 离线、确定、无需 GPU 或 API Key。它只证明接口、版本、控制流和降级可复现，不代表真实模型质量。
- 远程 Provider 只接受 HTTP/HTTPS URL；密钥仅从环境变量读取。
- Python、Node、pgvector 和 Redis 基础镜像同时保留可读标签并固定已验收的 manifest SHA-256，避免浮动标签静默改变构建输入；升级时需要显式改摘要并重跑本页验收。

## 单机生产覆盖配置

`.env.production.example` 是待替换模板，`infra/docker-compose.production.yml` 是叠加到基础 Compose 的生产覆盖文件：

~~~powershell
Copy-Item .env.production.example .env.production
# 编辑域名、CORS 来源和数据库密码后再继续
docker compose --env-file .env.production `
  --project-directory . `
  -f infra/docker-compose.yml `
  -f infra/docker-compose.production.yml `
  up -d --build --wait
~~~

覆盖配置会隐藏 PostgreSQL/Redis 宿主端口，给 API/Web 启用只读根文件系统、非 root 用户、删除 Linux capabilities、`no-new-privileges`、日志轮转、退出宽限期和资源上限。API 的上传对象仍写入专用命名卷。

部署方还必须完成这些外部责任：

- 用受信反向代理终止 HTTPS，并只把回环地址的 Web/API 暴露给代理；
- 用密钥管理器注入数据库和 Provider 密钥，不使用示例密码；
- 对 PostgreSQL 和对象存储卷建立备份、恢复演练与保留策略；
- 配置日志/Prometheus 采集、告警和磁盘容量监控；
- 若切换真实模型，先建立独立标注集并重新生成报告，不能沿用 Fixture 指标。

## 横向扩展边界

当前覆盖配置是单机、单 API 进程作品部署，不是 Kubernetes 或多区域方案。Redis 会话与限流状态可以共享，但进程内 Prometheus 累加器和熔断状态不能在多个 API worker 间聚合；在多副本前必须更换 multiprocess 指标实现、统一熔断观测，并增加共享对象存储。客户端地址限流也要求受信反向代理成为唯一入口，应用不会信任任意 `X-Forwarded-For`。

## CI 中的干净环境验收

`infrastructure` 作业从空 GitHub runner 启动完整 Compose，执行迁移、Fixture 导入、双向量索引和 `verify-fixture.ps1`，然后上传烟测 JSON。该流程不需要手工改数据库，也不调用付费或外部模型服务。
