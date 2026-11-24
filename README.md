# Catalist Meeting Intelligence Agent

[![Status](https://img.shields.io/badge/Status-Phase%2009%20Complete-brightgreen)](#system-overview)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791)](https://github.com/pgvector/pgvector)
[![License](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](./data/raw/CREDITS.txt)

The **Catalist Meeting Intelligence Agent** ingests hundreds of hours of raw multi-party meeting transcripts, builds an accurate, chronologically ordered temporal memory store, conducts multi-step research across meetings with exact word-for-word citations, and synthesizes pre-meeting briefs for project teams.

Evaluated on the **AMI Meeting Corpus** (138 real meetings, ~676,000 words across 35 design teams) and engineered to scale towards an enterprise corpus of **10,000+ meetings**.

---

## Deliverables & Submission Package (Phase 09)

1. **All 25 Benchmark Answers**: [`artifacts/answers.json`](./artifacts/answers.json)  
   *100% pass rate under deterministic validation (1–2 plain sentences, 1–3 citations, verbatim $\ge 6$-word single-turn quotations, spanning $\ge 2$ meetings per team).* Includes full TS3012 pre-meeting brief.
2. **Team TS3012 Pre-Meeting Briefing**: [`artifacts/briefing.md`](./artifacts/briefing.md)  
   *Complete 9-section pre-meeting intelligence briefing preceding meeting TS3012d with 7 verified citations.*
3. **Custom Evaluation Benchmark & Report**: [`artifacts/evaluation_report.md`](./artifacts/evaluation_report.md)  
   *10 cross-meeting challenge questions across 8 capabilities (100% accuracy), 3 deep failure case studies, empirical latency breakdown, and 1,000 / 10,000-meeting scalability analysis.*
4. **Final Technical Report**: [`technical_report.md`](./technical_report.md)  
   *Executive high-density architectural and empirical report.*
5. **3–5 Minute Live Demo Script**: [`docs/DEMO_SCRIPT.md`](./docs/DEMO_SCRIPT.md)  
   *Step-by-step walkthrough script for live presentation.*
6. **Technical Interview Defense Guide**: [`docs/INTERVIEW_DEFENSE_GUIDE.md`](./docs/INTERVIEW_DEFENSE_GUIDE.md)  
   *In-depth answers to 6 core architecture interview questions (hybrid retrieval, temporal graph, LangGraph loops, citation validation, contradictions, 10k scaling).*

---

## Core System Architecture

```text
[AMI Transcripts (138 files)] ──> [ParserService] ──> [TranscriptTurn / Speaker / Meeting Models]
                                                              │
                     ┌────────────────────────────────────────┴──────────────────────────┐
                     ▼                                                                   ▼
       [SentenceTransformers MiniLM-L6-v2]                                   [SQLite FTS5 / PostgreSQL FTS]
           384-dim Dense Embeddings                                              Lexical BM25 Search
                     │                                                                   │
                     └─────────────────────────┬─────────────────────────────────────────┘
                                               ▼
                              [HybridRetrievalService + RRF Fusion]
                                               │
                                 ┌─────────────┴─────────────┐
                                 ▼                           ▼
                     [TemporalMemoryService]     [LangGraph Research Agent]
                       (Decision Lineage Graph)    (Plan -> Retrieve -> Validate)
                                 │                           │
                                 └─────────────┬─────────────┘
                                               ▼
                                 [CitationValidationService]
                                   (Deterministic Boundary)
                                               │
                                 ┌─────────────┴─────────────┐
                                 ▼                           ▼
                       [REST API / Endpoints]        [React Dashboard]
```

### Key Highlights
- **100% Corpus Ingestion**: All 138 AMI meetings ingested (48,148 turns, 676,745 words) in 1,125.7 seconds (~18.8 minutes) on local CPU (~42.8 turns/sec).
- **Deterministic Citation Validation**: Enforces exact verbatim substring matching ($\ge 6$ words), single-turn boundaries, $\ge 2$ distinct meetings per team, and lexical claim overlap ($\ge 20\%$).
- **Append-Only Temporal Memory**: Tracks decision evolution (`CURRENT`, `SUPERSEDED`, `OPEN`, `RESOLVED`) without mutating historical records.
- **Hybrid Retrieval (RRF)**: Combines dense semantic vectors ($w=0.6$) with full-text BM25 search ($w=0.4$) using Reciprocal Rank Fusion ($k=60$).
- **LangGraph Stateful Research Agent**: 8-node state machine with loop guards, bounded retrieval, and automated fallback.
- **Modern React Dashboard**: Responsive web UI featuring Research Assistant, Citation Context Inspector, Temporal Memory Explorer, Decision Timeline, Briefing Viewer, and Ingestion Monitor.
- **Local-First & Zero Paid Keys**: Operates 100% locally with CPU embeddings and local LLM clients without requiring paid API keys.

---

## Repository Layout

```text
catalist-meeting-intelligence/
├── backend/            # Python 3.12, FastAPI, SQLAlchemy 2, LangGraph, Alembic, Pytest
│   ├── app/
│   │   ├── api/v1/     # REST route controllers (health, ingestion, memory, retrieval, agent, briefings)
│   │   ├── core/       # Typed config, logging, middleware, exceptions, tracing
│   │   ├── db/         # SQLAlchemy 2.x engine and session dependency
│   │   ├── models/     # Relational models (Team, Meeting, Speaker, Turn, Memory, Briefing, Session)
│   │   ├── schemas/    # Pydantic v2 schemas
│   │   ├── services/   # Business logic (Parser, Ingestion, Embedding, Memory, Retrieval, Agent, Briefing, Validator)
│   │   ├── cli.py      # Unified CLI tool
│   │   └── main.py     # FastAPI application factory
│   └── alembic/        # Database migrations (001 through 005)
├── frontend/           # React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query
├── data/               # Raw AMI corpus archives and processed SQLite/PostgreSQL database
├── artifacts/          # Final evaluation outputs (answers.json, briefing.md, evaluation_report.md)
└── docs/               # Architecture diagrams, ADRs, runbooks, specifications, demo script
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

#### Run Backend:
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate; Linux/macOS: source .venv/bin/activate
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

## Unified Command-Line Interface (CLI)

The backend provides a unified CLI via `python -m app.cli` (or `catalist` when installed):

### 1. Ingestion
```bash
# Ingest entire corpus and generate dense embeddings:
python -m app.cli ingest --dataset-path data/raw

# Ingest without embeddings for fast testing:
python -m app.cli ingest --dataset-path data/raw --skip-embeddings

# Force re-ingestion of existing meetings:
python -m app.cli ingest --dataset-path data/raw --force
```

### 2. Temporal Memory
```bash
# Extract temporal memories from a meeting:
python -m app.cli extract-memory --meeting-code TS3006d

# Search temporal memories:
python -m app.cli search-memory --team TS3006 --type DECISION --status CURRENT
```

### 3. Hybrid Retrieval
```bash
# Search across transcripts and temporal memories:
python -m app.cli retrieve "LCD screen speech recognition" --team TS3006 --limit 5
```

### 4. Agent Research & QA
```bash
# Ask a multi-meeting question with the LangGraph research agent:
python -m app.cli ask "Team TS3006 planned both an LCD screen and speech recognition. When the costs forced a cut, which of the two did they drop?" --team TS3006
```

### 5. Pre-Meeting Briefing
```bash
# Generate pre-meeting briefing for Team TS3012:
python -m app.cli brief --team TS3012 --save artifacts/briefing.md
```

---

## Automated Tests & Quality Gates

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

### Typecheck & Linting
```bash
# Backend linting and formatting
cd backend && ruff check .

# Frontend TypeScript check and production build
cd frontend && npm run build
```

---

## License & Attribution
The dataset utilized is the **AMI Meeting Corpus**, licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). See [`data/raw/CREDITS.txt`](./data/raw/CREDITS.txt) for academic citations.
