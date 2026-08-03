# Agent Reliability Arena

> A reproducible reliability arena for tool-using AI agents.

Agent Reliability Arena gives different models and agent runtimes the same synthetic
file, SQL, retrieval, approval, and adversarial tasks, then compares correctness,
safety, recovery, efficiency, latency, cost, and variance.

The project is built around one rule: **a pretty final answer is not enough**. Every
run happens in an isolated fixture, every model and tool turn becomes a replayable
trace, and the 100-point core score is deterministic.

## What is included

- `MinimalToolAgent`: a small ReAct/tool-calling baseline.
- `LangGraphAgent`: checkpointed state flow with retries and approval recovery.
- 12 versioned YAML scenarios across file, SQL, RAG, approval, and security families.
- A fail-closed tool gateway with no arbitrary shell, host filesystem, or real network.
- FastAPI, SSE, PostgreSQL/pgvector, Redis/Celery, and OpenTelemetry integration.
- React + TypeScript cockpit for tournaments, traces, comparisons, and leaderboards.
- A GitHub Pages demo mode that reads frozen, sanitized JSON and cannot call a model.

## Quick start

Requirements: Python 3.12, Node 20+, and Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Then open `http://127.0.0.1:5173`. The API binds to `127.0.0.1:8000` by default.

For a lightweight deterministic development loop without containers:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn arena.api:app --app-dir backend --reload --host 127.0.0.1
```

The fake provider uses no API key and makes no network request.

## Repository map

```text
backend/arena/     domain models, runtimes, tool gateway, scoring, persistence, API
scenarios/         public synthetic versioned YAML scenarios
frontend/          React/Vite cockpit and read-only demo mode
demo/              frozen sanitized tournament report
alembic/           database schema migrations
tests/             core, API, isolation, security, and deterministic replay tests
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for trust boundaries and the execution flow,
and [ROADMAP.md](ROADMAP.md) for the 30-workday quest map.

## Safety and data policy

Only synthetic fixtures belong in this public repository. `.env`, databases, raw
traces, model payloads, local reports, and keys are ignored. External model endpoints
are disabled unless explicitly allowed. Retrieved documents are always untrusted data.

## Score

| Dimension | Points |
|---|---:|
| Correctness | 50 |
| Safety and policy following | 25 |
| Recovery and idempotency | 15 |
| Step and token efficiency | 10 |

Latency, estimated cost, variance, and optional LLM judge results are displayed
separately. A judge can never modify the deterministic core score.

## License

[MIT](LICENSE)
