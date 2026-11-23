# Catalist Meeting Intelligence Agent

[![Phase](https://img.shields.io/badge/Phase%201-Foundation%20Ready-brightgreen)](#current-phase-status)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791)](https://github.com/pgvector/pgvector)
[![License](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](./data/raw/CREDITS.txt)

The **Catalist Meeting Intelligence Agent** ingests hundreds of hours of raw multi-party meeting transcripts, builds an accurate, chronologically ordered temporal memory store, conducts multi-step research across meetings with exact word-for-word citations, and synthesizes pre-meeting briefs for project teams.

Evaluated on the **AMI Meeting Corpus** (138 real meetings, ~676,000 words across 35 design teams) and engineered to scale towards an enterprise corpus of **10,000+ meetings**.

---

## Key Capabilities (System Roadmap)
- **Verbatim Speaker-Turn Evidence**: Every quote is verified word-for-word against the source transcript within a single speaker turn.
- **Temporal Memory Reasoning**: Distinguishes between early proposals, intermediate budget cuts, and final compromises across meeting series (a -> b -> c -> d).
- **Hybrid Retrieval**: Combines PostgreSQL Full-Text Search (lexical keyword matching) and dense vector search (384-dim `all-MiniLM-L6-v2` via `pgvector`) using Reciprocal Rank Fusion (RRF).
- **Stateful Research Agent**: Multi-hop reasoning loops with strict context bounds, checkpoints, and deterministic validation guards.
- **Automated Team Briefing**: Generates synthesized pre-meeting briefs highlighting confirmed decisions, changes along the way, open actions with owners, and ongoing disagreements.
- **Local-First & Zero Paid Keys**: Runs 100% locally with CPU embeddings and Ollama, or optionally with free-tier Gemini.

---

## Current Phase Status: Phase 1 Complete
Phase 1 establishes the engineering foundation, architecture baseline, and verified repository setup:
- [x] Layered FastAPI backend with health and readiness probes.
- [x] React + Vite + TypeScript frontend shell displaying real system status.
- [x] Docker Compose configuration for PostgreSQL 16 + pgvector with health checks.
- [x] Alembic migration suite configuring pgvector extension.
- [x] Typed settings with Pydantic v2 and safe `.env.example`.
- [x] Structured JSON logging, UUID request-ID middleware, and centralized exception handling.
- [x] Safe, optional LangSmith developer tracing integration.
- [x] Comprehensive documentation suite and ADRs under `docs/`.
- [x] Automated test suite passing for backend and frontend.

*Transcript parsing, embeddings, memory extraction, LangGraph research, and citation validation are scheduled for subsequent phases.*

---

## Architecture Summary
```text
catalist-meeting-intelligence/
├── backend/            # Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pytest
│   ├── app/
│   │   ├── api/v1/     # REST route controllers (health, ready)
│   │   ├── core/       # Typed config, logging, middleware, exceptions, tracing
│   │   ├── db/         # SQLAlchemy 2.x engine and session dependency
│   │   ├── models/     # Declarative models
│   │   ├── schemas/    # Pydantic v2 schemas
│   │   ├── services/   # Business logic (HealthService)
│   │   └── main.py     # FastAPI application factory
│   └── alembic/        # Database migrations (001_initial_pgvector)
├── frontend/           # React 18, TypeScript, Vite, Tailwind CSS, TanStack Query
├── data/               # Raw AMI corpus archives and questions.json
├── artifacts/          # Evaluations and submission outputs
└── docs/               # Architecture diagrams, ADRs, runbooks, specifications
```

---

## Prerequisites
- **Python 3.12+**
- **Node.js 18+** & **npm**
- **Docker** and **Docker Compose** (recommended for PostgreSQL 16 + pgvector)

---

## Quick Start

### 1. Environment Configuration
```bash
cp .env.example .env
```

### 2. Using Docker Compose (Recommended)
```bash
# Start PostgreSQL, Backend, and Frontend
docker-compose up -d --build

# Verify status
docker-compose ps
```
- Frontend UI: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`
- Readiness check: `http://localhost:8000/api/v1/ready`

### 3. Local Development (Non-Docker)

#### Start PostgreSQL:
Ensure PostgreSQL 16 with pgvector is accessible on port 5432, or start only the DB container:
```bash
docker-compose up -d db
```

#### Run Backend:
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate; On Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Run Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## Running Automated Tests

### Backend Tests (Pytest)
```bash
cd backend
pytest -v
```

### Frontend Tests (Vitest)
```bash
cd frontend
npm test -- --run
```

### Typecheck & Lint
```bash
# Backend linting
cd backend && ruff check .

# Frontend TypeScript check and build
cd frontend && npm run build
```

---

## Troubleshooting
- **Database Readiness Returns 503**: Ensure PostgreSQL is running and credentials in `.env` match `docker-compose.yml`.
- **Port Conflicts**: Change `BACKEND_PORT` or `POSTGRES_PORT` in `.env`.
- See [`docs/operations/local_runbook.md`](./docs/operations/local_runbook.md) for full operational guides.

---

## Next Steps
Proceed to **Phase 2: Dataset Ingestion and Preprocessing** (`docs/prompts/PHASE_02_DATASET_INGESTION.md`).

