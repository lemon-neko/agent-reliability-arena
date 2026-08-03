# Frozen demo data

The deployable snapshot lives at `frontend/public/data/report.json` so Vite copies it
without a runtime fetch from any backend. It contains synthetic scenario names,
sanitized sample trace events, and aggregate scores only.

Regenerate a release snapshot from a completed synthetic tournament, review it for
secrets and private payloads, then replace that file in one explicit commit. The demo
mode never reads local databases or model configuration.
