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
Alembic manages schema evolution:
```bash
cd backend

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Generate new migration autodetect
alembic revision --autogenerate -m "description"
```

---

## 4. Health Checks and Diagnostics
- **Liveness**: `curl -s http://localhost:8000/api/v1/health`
- **Readiness**: `curl -s http://localhost:8000/api/v1/ready`
- **Container Health**: Handled automatically in `docker-compose.yml` using `pg_isready` with 5s timeout.
