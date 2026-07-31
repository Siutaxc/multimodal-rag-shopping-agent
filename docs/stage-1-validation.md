# 阶段 1 验收记录

日期：2026-07-22  
工作区：`D:\CodexProjects\bytedance`

## 实测环境

- Windows 11 25H2，构建 26200.6584
- WSL 2.7.10.0，Linux 内核 6.18.33.2-2
- Docker Desktop 4.83.0，Docker Engine 29.6.2，Docker Compose 5.3.1
- Docker 程序目录：`D:\Apps\DockerDesktop`
- Docker WSL 数据目录：`D:\DockerData`
- Node.js 24.14.0，npm 11.9.0
- Python 3.13.7
- PostgreSQL 16.14，pgvector 0.8.5
- Redis 7.4

Docker Desktop 不依赖单独安装 Ubuntu。镜像、容器和数据库卷均存储在 D 盘的 Docker WSL 虚拟磁盘中；C 盘仅保留 Docker 安装器要求的 CLI 插件和少量用户配置。

## 已执行检查

| 检查 | 结果 |
|---|---|
| Docker Compose 构建与启动 | 通过，Web、API、PostgreSQL、Redis 四个容器均为 `healthy` |
| API 就绪检查 | 通过，`postgres`、`pgvector`、`redis` 均为 `ok` |
| PostgreSQL / pgvector | PostgreSQL 16.14，vector 扩展 0.8.5 |
| Redis | `PING` 返回 `PONG` |
| 基础设施集成测试 | 1 通过 |
| Ruff | 通过 |
| mypy strict | 12 个源码/测试文件通过 |
| pytest 单元测试 | 7 通过，1 个集成测试按标记排除并另行实测通过 |
| ESLint | 通过，0 warning |
| TypeScript strict | 通过 |
| Vitest | 1 个前端测试通过 |
| Next.js 生产构建 | 通过，首页静态预渲染 |
| Web HTTP 烟测 | `http://localhost:3000` 返回 200，页面包含 ShopLens |
| API HTTP 烟测 | `http://localhost:8000/api/v1/health/ready` 返回 ready |
| 依赖不可用降级 | 单元测试确认返回 503，并逐项报告依赖状态 |

## 现场修复

首次在真实 Docker 环境验收时发现并修复了四个问题：

1. Compose 的 API/Web 构建上下文多退了一层，导致 Docker 在工作区外查找源码。
2. pgvector 初始化 SQL 的绑定路径未包含 `infra`，导致首次数据库初始化无法找到脚本。
3. Web Dockerfile 假设 workspace 子目录存在独立 `node_modules`，与 npm 实际的根目录依赖提升行为不一致。
4. psycopg 异步连接不支持 Windows 默认 Proactor 事件循环；探针改为通过线程执行同步连接，保持事件循环非阻塞并同时兼容 Windows 与 Linux。

## 阶段验收对照

| 蓝图验收项 | 状态 | 证据 |
|---|---|---|
| 一条命令启动所有基础服务 | 已通过 | Compose 成功构建并启动四个健康容器 |
| 浏览器通过 HTTP 打开前端占位页 | 已通过 | 首页返回 200 |
| API OpenAPI 文档可访问 | 已通过 | `/docs` 与 OpenAPI 已配置，API 容器健康 |
| 数据库已启用 vector 扩展 | 已通过 | PostgreSQL 查询返回 pgvector 0.8.5 |
| 后端单测、前端检查和构建通过 | 已通过 | `npm run check` 完整通过 |
| README 可指导新环境从零启动 | 已完成 | 根 README 包含环境要求、启动、检查和端点说明 |

## 已知非阻塞事项

- 当前登录会话创建于安装 Docker 之前，因此旧终端令牌尚未包含 `docker-users` 组；注销重新登录或重启后，普通 PowerShell 会获得 Docker 命名管道权限。
- 通过 npm 官方注册表执行审计时报告 1 个中等、2 个高风险告警，来自 Next.js 16.2.10 的 `postcss` 与 `sharp` 传递依赖。当前最新版 Next.js 16.2.11 仍声明相关旧依赖范围，`npm audit fix` 给出的降级方案不适用。本项目暂不强制覆盖上游依赖；在进入会处理不可信图片的阶段 5 前必须重新评估并升级。

## 结论

阶段 1 的代码、容器基础设施、HTTP 服务、pgvector、Redis、单元测试、集成测试和生产构建已全部实测通过，可以进入阶段 2。
