# 阶段 1 验收说明

本阶段只建立可启动、可测试的工程底座，不包含商品模型、数据导入或检索实现。

## 服务边界

- **web**：Next.js App Router 占位页，仅提供指向 API 文档和存活检查的 HTTP 链接。
- **api**：FastAPI 应用、OpenAPI 文档、进程存活检查和依赖就绪检查。
- **postgres**：PostgreSQL 16，并由初始化脚本启用 **vector** 扩展。
- **redis**：Redis 7.4，作为后续缓存和异步任务的基础设施。

## 健康检查语义

| 路径 | 成功条件 | 失败行为 |
|---|---|---|
| /api/v1/health/live | API 进程可响应 | 进程不可访问 |
| /api/v1/health/ready | PostgreSQL 可查询、vector 已启用、Redis PING 成功 | HTTP 503，并逐项返回状态 |

为兼容阶段任务中的简写，/health/live 与 /health/ready 也可访问，但不会重复出现在 OpenAPI 中。

## 可重复验收

1. 运行 **npm run stack:up** 构建并启动四个服务。
2. 打开 http://localhost:3000 和 http://localhost:8000/docs。
3. 请求 http://localhost:8000/api/v1/health/ready，确认三个检查均为 **ok**。
4. 运行 **npm run check**，执行后端 lint、类型检查、单测以及前端 lint、类型检查、单测和生产构建。
5. 设置 SHOPLENS_RUN_INTEGRATION=1 后运行集成测试，可复用 API 的真实依赖探针确认 pgvector 与 Redis。
