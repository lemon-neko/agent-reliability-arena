.PHONY: up down test lint backend frontend demo security

up:
	docker compose up --build

down:
	docker compose down

test:
	.venv/bin/pytest --cov --cov-report=term-missing

lint:
	.venv/bin/ruff check backend tests tools
	cd frontend && pnpm build

backend:
	.venv/bin/uvicorn arena.api:app --app-dir backend --reload --host 127.0.0.1

frontend:
	cd frontend && pnpm dev

demo:
	cd frontend && VITE_DEMO_MODE=true pnpm build --mode demo

security:
	.venv/bin/python tools/security_guard.py
