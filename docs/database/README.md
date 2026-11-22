# Database Setup & Migration Guide

## Engine & Driver
- **Database**: PostgreSQL 16
- **Extension**: `pgvector`
- **Driver**: `psycopg` (v3) with SQLAlchemy 2.x dialect (`postgresql+psycopg://...`)
- **Migration Tool**: Alembic

## Baseline Migration (Phase 1)
Migration `001_initial_pgvector.py` establishes the baseline extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
And provides full reversible downgrade:
```sql
DROP EXTENSION IF EXISTS vector;
```

## Running Migrations Locally
```bash
cd backend
alembic upgrade head
```
