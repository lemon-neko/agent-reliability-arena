# API 应用

本目录包含 Agent Reliability Arena 的 Python 应用。

| 位置 | 职责 |
|---|---|
| `src/arena/domain/` | 稳定领域类型与确定性评分 |
| `src/arena/application/` | Run 与 Tournament 用例编排 |
| `src/arena/runtime/` | Agent、Provider、Tool、Sandbox、Scenario、Trace |
| `src/arena/infrastructure/` | 配置、Store、Celery、OpenTelemetry |
| `src/arena/interfaces/http/` | FastAPI REST/SSE 控制面 |
| `migrations/` | Alembic 数据库迁移 |
| `tests/` | 后端、API、安全与确定性测试 |

从仓库根目录运行 `make dev-api`、`make test-api` 或 `make check`。架构解释见 [系统架构](../../docs/architecture/overview.md)，扩展步骤见 [实现指南](../../docs/development/implementation.md)。
