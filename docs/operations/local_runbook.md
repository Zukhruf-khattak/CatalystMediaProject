# Operations Runbook & Troubleshooting

## Common Local Development Scenarios

### 1. Database Connection Refused (Readiness 503)
- **Symptom**: `/api/v1/ready` returns 503 with `"database": false`.
- **Cause**: PostgreSQL is not running or credentials in `.env` do not match.
- **Fix**:
  1. Start Docker container: `docker-compose up -d db`.
  2. Verify PostgreSQL logs: `docker-compose logs db`.
  3. Confirm `DATABASE_URL` matches Docker credentials in `.env`.

### 2. Port Conflicts
- **Port 8000 (Backend)**: If port 8000 is taken, update `BACKEND_PORT=8001` in `.env` and `VITE_API_BASE_URL=http://localhost:8001` in frontend.
- **Port 5173 (Frontend)**: Vite automatically suggests 5174 if 5173 is busy.
- **Port 5432 (PostgreSQL)**: If a local PostgreSQL instance is running on 5432, map a different host port in `docker-compose.yml` (e.g. `5433:5432`) and update `DATABASE_URL`.

### 3. Running Without Docker
- If Docker daemon is unavailable, developer can use a local PostgreSQL installation or run tests using Pytest with SQLite test database fixture overrides.

