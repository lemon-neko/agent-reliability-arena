.PHONY: setup dev-api dev-web test-api test-web lint-api check-scenarios \
	check-governance export-scenario-schema demo security check compose-up compose-down new-change

PYTHON := .venv/bin/python
PIP := .venv/bin/pip

setup:
	python3.12 -m venv .venv
	$(PIP) install -e 'apps/api[dev]'
	cd apps/web && pnpm install --frozen-lockfile
	cd apps/web && pnpm exec playwright install chromium

dev-api:
	.venv/bin/uvicorn arena.interfaces.http.app:app --app-dir apps/api/src --reload --host 127.0.0.1 --port 8000

dev-web:
	cd apps/web && pnpm dev

test-api:
	cd apps/api && ../../.venv/bin/pytest --cov --cov-report=term-missing

test-web:
	cd apps/web && pnpm build && pnpm test:e2e

lint-api:
	cd apps/api && ../../.venv/bin/ruff check src tests migrations ../../tools

export-scenario-schema:
	$(PYTHON) tools/export_scenario_schema.py

check-scenarios:
	$(PYTHON) tools/export_scenario_schema.py --check

check-governance:
	$(PYTHON) tools/check_project_map.py
	$(PYTHON) tools/check_docs.py
	$(PYTHON) tools/check_change_note.py

demo:
	cd apps/web && VITE_DEMO_MODE=true pnpm build --mode demo

security:
	$(PYTHON) tools/security_guard.py

check: lint-api test-api check-scenarios check-governance security test-web

compose-up:
	docker compose up --build

compose-down:
	docker compose down

new-change:
	$(PYTHON) tools/new_change.py --slug "$(SLUG)" --type "$(TYPE)"
