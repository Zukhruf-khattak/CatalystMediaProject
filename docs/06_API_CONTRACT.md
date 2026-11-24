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

## 3. Phase 4 Implemented Endpoints: Retrieval

### 3.1 POST `/api/v1/retrieval/search`
**Purpose**: Execute hybrid search across transcript turns and temporal memories, fusing lexical and semantic signals with Reciprocal Rank Fusion (RRF).

**Request Body (`RetrievalRequest`)**:
```json
{
  "query": "Why did the team decide against using fruit shapes for the remote control?",
  "team_code": "TS3006",
  "meeting_codes": ["TS3006a", "TS3006b", "TS3006c", "TS3006d"],
  "speaker_labels": ["Speaker A", "Speaker B"],
  "memory_types": ["DECISION", "DISAGREEMENT"],
  "memory_statuses": ["current", "superseded"],
  "method": "hybrid",
  "limit": 10,
  "rrf_k": 60,
  "include_memories": true,
  "include_turns": true,
  "expand_temporal_graph": true
}
```

**Response (200 OK — `EvidencePackResponse`)**:
```json
{
  "query": "Why did the team decide against using fruit shapes for the remote control?",
  "processed_query": {
    "raw_query": "Why did the team decide against using fruit shapes for the remote control?",
    "cleaned_query": "team decide against fruit shapes remote control",
    "extracted_team": "TS3006",
    "extracted_meetings": [],
    "extracted_speakers": [],
    "extracted_roles": [],
    "extracted_topics": ["shape", "battery", "casing"],
    "is_temporal_query": false,
    "suggested_method": "hybrid"
  },
  "retrieval_method": "hybrid",
  "total_turn_candidates": 8,
  "total_memory_candidates": 2,
  "turns": [
    {
      "turn_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "meeting_id": "TS3006b",
      "team_id": "TS3006",
      "turn_index": 42,
      "speaker_label": "Speaker B",
      "speaker_role": "Industrial Designer",
      "start_time": "00:15:30",
      "text": "I think the fruit shapes are a bit childish and too expensive to mould.",
      "score": 0.0328,
      "channel": "hybrid"
    }
  ],
  "memories": [
    {
      "memory_id": "e4d3c2b1-a098-7654-3210-fedcba987654",
      "memory_type": "DECISION",
      "statement": "The team decided against fruit vegetable shapes in favor of an ergonomic curve.",
      "quote": "fruit shapes are a bit childish and too expensive to mould",
      "status": "current",
      "meeting_id": "TS3006b",
      "meeting_order": 2,
      "speaker_label": "Speaker B",
      "score": 0.0312,
      "channel": "temporal_memory",
      "linked_memory_ids": ["f5e4d3c2-b1a0-9876-5432-10fedcba9876"]
    }
  ],
  "retrieved_at": "2026-11-23T19:30:00Z"
}
```

### 3.2 POST `/api/v1/retrieval/process-query`
**Purpose**: Deterministically analyze a natural language query, extracting team codes, meeting codes, speaker labels/roles, domain topics, temporal intent, and cleaned search terms.

**Request Body**:
```json
{
  "query": "In TS3006b, what did Speaker C say about the scroll wheel?"
}
```

**Response (200 OK — `ProcessedQuery`)**:
```json
{
  "raw_query": "In TS3006b, what did Speaker C say about the scroll wheel?",
  "cleaned_query": "scroll wheel",
  "extracted_team": "TS3006",
  "extracted_meetings": ["TS3006b"],
  "extracted_speakers": ["Speaker C"],
  "extracted_roles": [],
  "extracted_topics": ["scroll wheel", "interface"],
  "is_temporal_query": false,
  "suggested_method": "hybrid"
}
```

---

## 4. Agent Research & Citation Validation Endpoints (Phase 5 & 6)

### 4.1 POST `/api/v1/agent/query`
**Purpose**: Run the LangGraph stateful agent to research a user question with deterministic citation and evidence validation.

**Request Body (`AgentQueryRequest`)**:
```json
{
  "question": "What casing material did Team ES2003 switch from and to?",
  "team_code": "ES2003",
  "session_id": "optional-uuid"
}
```

**Response (200 OK — `AgentQueryResponse`)**:
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "question": "What casing material did Team ES2003 switch from and to?",
  "team_code": "ES2003",
  "answer": "Team ES2003 initially leaned towards a double curved rubber case in ES2003b. In ES2003d, they switched to standard plastic because rubber moulding exceeded the cost budget.",
  "is_sufficient": true,
  "citations": [
    {
      "meeting_id": "ES2003b",
      "team_id": "ES2003",
      "turn_id": "turn-uuid-1",
      "speaker_label": "Speaker B",
      "speaker_role": "Industrial Designer",
      "quote": "leaned towards a double curved rubber case"
    },
    {
      "meeting_id": "ES2003d",
      "team_id": "ES2003",
      "turn_id": "turn-uuid-2",
      "speaker_label": "Speaker B",
      "speaker_role": "Industrial Designer",
      "quote": "switched to standard plastic because rubber moulding exceeded the cost budget"
    }
  ],
  "validation_status": "PASSED",
  "validation_errors": [],
  "supporting_meetings": ["ES2003b", "ES2003d"],
  "iteration": 1,
  "steps_taken": [
    "input_validation",
    "query_analysis",
    "retrieval_planning",
    "tool_execution",
    "evidence_assessment",
    "answer_generation",
    "citation_validation",
    "final_response"
  ]
}
```

---

## 5. Endpoints Summary and Implementation Status

| Endpoint | Method | Phase | Status | Purpose |
|---|---|---|---|---|
| `/api/v1/health` | GET | Phase 1 | Completed | Liveness probe |
| `/api/v1/ready` | GET | Phase 1 | Completed | Readiness probe checking PostgreSQL |
| `/api/v1/ingestion/jobs` | POST/GET | Phase 2 | Completed | Ingestion runner & job status |
| `/api/v1/memory/search` | POST | Phase 3 | Completed | Temporal memory search & filtering |
| `/api/v1/retrieval/search` | POST | Phase 4 | Completed | Hybrid lexical + semantic search endpoint |
| `/api/v1/retrieval/process-query` | POST | Phase 4 | Completed | Deterministic query parsing endpoint |
| `/api/v1/agent/query` | POST | Phase 5-6 | Completed | Stateful research agent query with citation validation |
| `/api/v1/agent/sessions/{id}/query` | POST | Phase 5 | Completed | Multi-turn session-aware agent query |
| `/api/v1/agent/sessions/{id}` | GET | Phase 5 | Completed | Session turn history retrieval |
| `/api/v1/agent/status` | GET | Phase 5 | Completed | Agent status & runtime telemetry |
| `/api/v1/brief/{team_id}` | GET/POST | Phase 7 | Planned | Generate pre-meeting brief for specified team |
| `/api/v1/evaluations` | GET | Phase 9 | Planned | View evaluation benchmark results |

