# 07 — Testing and Evaluation Plan

## 1. Testing Strategy and Layers

The testing strategy encompasses four rigorous layers:

```mermaid
flowchart TD
    Unit["Layer 1: Unit Tests (Services, schemas, configs, validators)"]
    Integration["Layer 2: Integration Tests (FastAPI routes, DB sessions, Alembic)"]
    E2E["Layer 3: Agentic E2E Tests (LangGraph loops, citation validation)"]
    EvalBenchmark["Layer 4: Evaluation Benchmark (25 Supplied + 10 Author-Verified)"]

    Unit --> Integration
    Integration --> E2E
    E2E --> EvalBenchmark
```

### 1.1 Backend Foundation Tests (Phase 1)
- Application startup and route discovery.
- Health endpoint returns 200 and safe metadata.
- Readiness endpoint accurately detects database up vs. database down.
- Request ID middleware generates UUID when absent, echoes valid incoming ID.
- Centralized exception handlers return standardized error payloads without tracebacks.
- Configuration validation fails on invalid types or missing required values with clear messages.
- LangSmith unconfigured / disabled mode runs cleanly without error.
- Database session dependency can be overridden in test fixtures.

### 1.2 Ingestion & Parsing Tests (Phase 2)
- Zip slip and directory traversal prevention.
- Deterministic header and roster parsing.
- Verbatim speech text preservation.
- Meeting-scoped speaker uniqueness.
- Fault isolation via database transaction savepoints.
- Offline dense embedding generation.

### 1.3 Temporal Memory Tests (Phase 3)
- `test_evidence_validator.py`: Verbatim quote verification, minimum 6 words threshold, rejection of modified/fabricated quotes, speaker label consistency, action owner validation.
- `test_temporal_reasoning.py`: Decision supersession (meeting `a` superseded by meeting `c`), action resolution, disagreement reopening, ambiguous change preservation, team isolation.
- `test_memory_extraction.py`: Mocked LLM extraction flow, schema validation, quote rejection audit logging, duplicate prevention, idempotency.
- `test_memory_retrieval.py`: Paginated retrieval, team filtering, type/status filtering, statement and quote query filtering, eager relationship loading.
- `test_memory_api.py`: Extraction trigger validation, run status inspection, search filtering, single memory retrieval by UUID.

### 1.4 Hybrid Retrieval Tests (Phase 4)
- `test_query_processor.py`: AMI team code extraction (`TS3006`), meeting code extraction (`TS3006b`), speaker label/role parsing (`Speaker C`, `Project Manager`), domain keyword extraction, temporal indicator detection (`initially`, `eventually`, `change`), and stopword removal.
- `test_hybrid_retrieval.py`: Reciprocal Rank Fusion ($k=60$) mathematics, channel weight tuning ($w_{kw}, w_{vec}$), keyword-only execution, vector-only execution, hybrid fusion, metadata filtering (`team_code`, `meeting_codes`, `speaker_labels`), and candidate limit enforcement.
- `test_temporal_retrieval.py`: Temporal memory retrieval integration, relationship graph traversal (linking historical decisions with superseding decisions), and open disagreement isolation.
- `test_retrieval_api.py`: Integration testing of `/api/v1/retrieval/search` and `/api/v1/retrieval/process-query` endpoints with FastAPI `TestClient`, validation error handling, and parameter overrides.
- `test_retrieval_evaluation.py`: Metric computation correctness (`Recall@K`, `Precision@K`, `MRR`), synthetic ranking fixtures, and benchmark suite verification.

### 1.5 Frontend Foundation Tests (Phase 1)
- Overview page renders product title, mission, and workflow pipeline.
- System status panel handles loading, healthy, degraded, and network failure states.
- TanStack Query hook handles polling and error catching.
- Client-side navigation renders routes without unhandled exceptions.

---

## 2. Assessment Benchmark Protocol (Phase 9)

### 2.1 The 25 Supplied Assessment Questions
- Evaluated against `questions.json`.
- Graded on:
  1. Factual accuracy of the 1–3 sentence answer.
  2. Citation validity: exact quote matching stored turn, >= 6 words, correct `meeting_id`.
  3. Strict adherence to submission JSON schema.

### 2.2 The 10 Independently Authored & Manually Verified Questions
- Written by the author and verified by manual transcript inspection.
- Provides a controlled ground-truth testbed to evaluate agent recall, precision, and multi-hop reasoning.

### 2.3 Failure Analysis Protocol
- Three documented edge cases and failure modes analyzed with root causes and corrective mitigations.

### 2.4 Retrieval Evaluation Benchmark Results (Phase 4)
The hybrid retrieval engine was benchmarked against the 25 multi-meeting questions in `data/raw/questions.json` across 10 evaluation runs:

| Metric | Keyword Only | Dense Vector Only | Hybrid RRF ($w=1.0/1.0, k=60$) | Target / Benchmark |
|---|---|---|---|---|
| **Recall@5** | 0.4400 | 0.6800 | **0.6800** | $\ge 0.60$ |
| **Recall@10** | 0.5200 | 0.8200 | **0.8200** | $\ge 0.75$ |
| **Precision@5** | 0.7000 | 0.8000 | **0.8000** | $\ge 0.70$ |
| **Precision@10** | 0.8000 | 0.9000 | **0.9000** | $\ge 0.80$ |
| **MRR** | 0.8000 | 0.9000 | **0.9000** | $\ge 0.85$ |
| **Multi-Meeting Coverage** | 50.0% | 90.0% | **90.0%** | $\ge 80.0\%$ |
| **Mean Latency (Warm)** | 5.42 ms | 98.40 ms | **97.00 ms** | $< 250$ ms |

For the complete evaluation report, error analysis, and tuning experiments, see [RETRIEVAL_EVALUATION.md](./evaluation/RETRIEVAL_EVALUATION.md).
