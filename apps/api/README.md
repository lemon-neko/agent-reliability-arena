# API 应用

本目录包含 Agent Reliability Arena 的 Python 应用。

| 位置 | 职责 |
|---|---|
| `src/arena/domain/` | Arena 与风险评估领域类型、评分和安全门禁 |
| `src/arena/application/` | Run、Assessment、报告与证明包编排 |
| `src/arena/runtime/` | Agent、Step Protocol、Tool、Sandbox、Scenario、Trace |
| `src/arena/infrastructure/` | 配置、Store、Celery、OpenTelemetry |
| `src/arena/interfaces/http/` | FastAPI REST/SSE 控制面 |
| `migrations/` | Alembic 数据库迁移 |
| `tests/` | 后端、API、安全与确定性测试 |

从仓库根目录运行 `make dev-api`、`make test-api` 或 `make check`。外部 Agent 接入见 [ara-step/1 协议](../../docs/development/http-agent-protocol.md)，架构解释见 [系统架构](../../docs/architecture/overview.md)。
