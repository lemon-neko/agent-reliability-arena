# Docker 完整模式

```bash
cp .env.example .env
make compose-up
```

Compose 启动 PostgreSQL/pgvector、Redis、Alembic migration、FastAPI、Celery Worker 和 Nginx Web。公开端口默认只绑定 `127.0.0.1`。

```bash
docker compose config
make compose-down
```

数据库结构由 `apps/api/migrations/` 管理；容器内场景来自 `packages/scenarios/catalog/`。
