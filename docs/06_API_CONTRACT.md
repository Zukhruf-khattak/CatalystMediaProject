# 06 — API Contract

## 1. Overview
The Catalist Meeting Intelligence API is served over HTTP/JSON under the prefix `/api/v1`. All endpoints return standard HTTP status codes and attach an `X-Request-ID` response header for end-to-end tracing.

---

## 2. Phase 1 Implemented Endpoints

### 2.1 GET `/api/v1/health`
**Purpose**: Liveness probe. Verifies application process is running. Never queries external dependencies. Never leaks credentials.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "app_name": "Catalist Meeting Intelligence",
  "version": "0.1.0",
  "environment": "development"
}
```

### 2.2 GET `/api/v1/ready`
**Purpose**: Readiness probe. Verifies database connectivity with a strict 5.0-second timeout.

**Response when Ready (200 OK)**:
```json
{
  "status": "ready",
  "database": true,
  "app_name": "Catalist Meeting Intelligence",
  "version": "0.1.0",
  "environment": "development"
}
```

**Response when Degraded (503 Service Unavailable)**:
```json
{
  "status": "degraded",
  "database": false,
  "app_name": "Catalist Meeting Intelligence",
  "version": "0.1.0",
  "environment": "development"
}
```

### 2.3 GET `/`
**Purpose**: Root service information and OpenAPI pointer.

**Response (200 OK)**:
```json
{
  "message": "Welcome to Catalist Meeting Intelligence API",
  "docs_url": "/docs",
  "health_url": "/api/v1/health",
  "readiness_url": "/api/v1/ready",
  "version": "0.1.0"
}
```

---

## 3. Planned Endpoints (Future Phases)

| Endpoint | Method | Phase | Purpose |
|---|---|---|---|
| `/api/v1/ingest` | POST | Phase 2 | Trigger or resume transcript ingestion pipeline |
| `/api/v1/ingest/status` | GET | Phase 2 | Ingestion progress and statistics |
| `/api/v1/meetings` | GET | Phase 2 | List ingested meetings with pagination |
| `/api/v1/search` | POST | Phase 4 | Hybrid lexical + semantic search endpoint |
| `/api/v1/research/query` | POST | Phase 5 | Execute LangGraph research agent on a question |
| `/api/v1/citations/validate`| POST | Phase 6 | Deterministically validate quote against database |
| `/api/v1/brief/{team_id}` | GET/POST | Phase 7 | Generate pre-meeting brief for specified team |
| `/api/v1/evaluations` | GET | Phase 9 | View evaluation benchmark results |
