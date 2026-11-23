# 09 — Deployment and Operations

## 1. Local Developer Workflow

### Prerequisites
- Python 3.12+ (or `uv`)
- Node.js 18+ & npm
- Docker & Docker Compose (optional for local non-Docker development; recommended for PostgreSQL + pgvector)

### Local Non-Docker Startup
1. **Environment Setup**:
   ```bash
   cp .env.example .env
   ```
2. **Backend Startup**:
   ```bash
   cd backend
   uv pip install -e ".[dev]"
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. **Frontend Startup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 2. Docker Compose Deployment
```bash
# Start PostgreSQL, Backend, and Frontend containers
docker-compose up -d --build

# Inspect status
docker-compose ps

# Tail logs
docker-compose logs -f

# Shutdown services and preserve named database volume
docker-compose down
```

---

## 3. Database Migration Operations
Alembic manages schema evolution across all phases:
```bash
cd backend
# Upgrade to latest schema
alembic upgrade head

# Inspect SQL DDL offline without connecting to PostgreSQL
alembic upgrade head --sql
```

Available Migrations:
- `001_initial_pgvector`: Enable PostgreSQL `pgvector` extension.
- `002_dataset_ingestion_schema`: Tables for `teams`, `meetings`, `speakers`, `transcript_turns`, `ingestion_jobs`.
- `003_temporal_memory_schema`: Tables for `memories`, `memory_relationships`, `memory_extraction_runs`.

---

## 4. Operational CLI Commands

### Dataset Ingestion
```bash
python -m app.cli ingest --dataset-path data/raw --skip-embeddings
```

### Temporal Memory Extraction
```bash
# Extract memories chronologically for an entire team
python -m app.cli extract-memory --team-code TS3006

# Extract memories for a single meeting
python -m app.cli extract-memory --meeting-code TS3006a

# Force re-extraction
python -m app.cli extract-memory --meeting-code TS3006a --force
```

### Memory Search
```bash
python -m app.cli search-memory --team-code TS3006 --type DECISION --status current
```

### Hybrid Retrieval Search
```bash
# Execute hybrid retrieval for a question
catalist retrieve --query "Why did the team decide against using fruit shapes?" --team-code TS3006 --method hybrid --limit 10

# Keyword-only retrieval
catalist retrieve --query "kinetic battery" --method keyword --limit 5

# Vector-only retrieval
catalist retrieve --query "remote control casing material" --method vector --limit 5
```

For operational recovery, index maintenance, and latency monitoring runbooks, refer to [RETRIEVAL_RUNBOOK.md](./operations/RETRIEVAL_RUNBOOK.md).
