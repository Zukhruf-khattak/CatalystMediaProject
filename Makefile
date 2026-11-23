.PHONY: help setup run-backend run-frontend docker-up docker-down docker-logs test-backend test-frontend test lint format migrate migrate-down

help:
	@echo "Catalist Meeting Intelligence Agent - Available Commands:"
	@echo "  make setup          - Install backend and frontend dependencies"
	@echo "  make run-backend    - Run FastAPI backend locally with uvicorn"
	@echo "  make run-frontend   - Run Vite React frontend locally"
	@echo "  make docker-up      - Start all services with Docker Compose"
	@echo "  make docker-down    - Stop Docker Compose services"
	@echo "  make docker-logs    - Tail Docker Compose logs"
	@echo "  make test-backend   - Run Pytest test suite for backend"
	@echo "  make test-frontend  - Run Vitest test suite for frontend"
	@echo "  make test           - Run all tests (backend and frontend)"
	@echo "  make lint           - Lint backend and frontend code"
	@echo "  make format         - Format backend code with ruff"
	@echo "  make migrate        - Apply Alembic migrations"
	@echo "  make migrate-down   - Rollback the last Alembic migration"

setup:
	cd backend && uv pip install -e ".[dev]"
	cd frontend && npm install

run-backend:
	cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test -- --run

test: test-backend test-frontend

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

format:
	cd backend && ruff format .

migrate:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade -1

