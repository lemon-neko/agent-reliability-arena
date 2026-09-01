# API 区域规则

先遵守根目录 [AGENTS.md](../../AGENTS.md)。本目录只补充后端约束。

- 依赖方向为 `domain → application → runtime/infrastructure → interfaces`；内层不得导入 FastAPI、Celery 或 SQLAlchemy 适配层。
- `ArenaEngine` 保持与 HTTP、Celery、具体数据库解耦；外部副作用只经 Provider、Tool Gateway 和 Store 边界。
- 路由只做协议校验和应用服务调用，不在路由中实现评测逻辑。
- 数据结构变化必须新增 Alembic migration；应用启动不得成为生产 Schema 的唯一来源。
- 后端修改至少运行 `make test-api`，安全、配置、迁移或执行边界变化必须运行 `make check`。
