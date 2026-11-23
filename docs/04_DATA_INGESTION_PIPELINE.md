# Data Ingestion and Indexing Pipeline

**Phase:** Phase 2 — Dataset Discovery, Transcript Ingestion & Indexing  
**Status:** Completed & Operational  
**Module:** `backend/app/services/ingestion_service.py`, `backend/app/services/parser_service.py`, `backend/app/services/archive_service.py`, `backend/app/services/embedding_service.py`

---

## 1. Overview and Design Principles

The Catalist Ingestion Pipeline ingests raw multi-meeting AMI transcripts into a structured, indexed, canonical source-of-truth database. It is engineered with three core invariants:

1. **Exact Ground-Truth Preservation:** The `raw_text` of each speaker turn is immutable and verbatim. Disfluencies ("um", "uh"), interruptions, false starts, and speech punctuation are strictly preserved to enable exact citation matching in later phases.
2. **Idempotency & Resumability:** Content-based SHA-256 checksums prevent duplicate ingestion. Re-running the pipeline skips already ingested, unchanged transcripts in sub-millisecond time. A `--force` flag enables controlled re-ingestion.
3. **Meeting-Level Transactional Isolation:** Ingestion processes each meeting in an isolated database transaction. If a corrupted file or parse error occurs, that meeting rolls back cleanly without rolling back previously committed meetings, and the error is recorded in `ingestion_jobs.errors_json`.

---

## 2. Pipeline Stages

```
[Raw ZIP Archive / .txt Directory]
              │
              ▼
   [Archive Safety & Traversal Check]
              │
              ▼
   [Deterministic AMI Transcript Parser]
              │
              ├──> [Team Record (Upsert)]
              ├──> [Meeting Record (Metadata, SHA-256, Raw Text)]
              ├──> [Speaker Records (Meeting-Scoped)]
              │
              ▼
   [Local Dense Embedding Generator (all-MiniLM-L6-v2, 384d, CPU)]
              │
              ▼
   [Transcript Turn Persistence]
              ├──> raw_text (Immutable ground-truth)
              ├──> normalized_text (Cleaned for search)
              ├──> embedding (vector(384) with HNSW index)
              └──> search_vector (PostgreSQL tsvector with GIN index)
              │
              ▼
   [Ingestion Job Audit & Progress Update]
```

### Stage 1: Archive Safety & Discovery
- Safe ZIP extraction defending against **Zip Slip** (path traversal `..`, absolute paths, symlinks).
- Enforces configurable size limits (max 50 MB compressed, max 500 files).
- Whitelists only safe data file extensions (`.txt`, `.json`).
- Staged into temporary directory before atomic file promotion.

### Stage 2: Deterministic Transcript Parsing
- Extracts metadata header: `Meeting:`, `Team:`, `Meeting number:`, `Speakers:`, `Times:`, `Source:`.
- Splits speaker turns using strict regex: `^(\d{2}:\d{2}:\d{2})\s+(Speaker\s+[A-D])\b`.
- Associates all subsequent utterance lines to the active speaker turn.
- Calculates total turns, word counts, and start/end timestamps.
- Flags and logs non-monotonic timestamps and empty turns without crashing.

### Stage 3: Local Dense Vector Generation
- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- **Execution:** 100% local CPU inference, lazy-loaded singleton.
- **Offline Reliability:** Enforces `HF_HUB_OFFLINE=1` to eliminate network latency and timeouts.
- **Batching:** Configurable batch size (default: 32).
- **Zero Vector:** Safely returns a 384-dimensional zero vector for empty/whitespace turns.
- **Skip Flag:** `--skip-embeddings` flag allows rapid text-only ingestion during development and tests.

### Stage 4: PostgreSQL Indexing & Storage
- Foreign keys with `ON DELETE CASCADE` ensure referential integrity.
- **PostgreSQL Full-Text Search:** Native `tsvector` column maintained via PostgreSQL C-trigger `tsvector_update_trigger(search_vector, 'pg_catalog.english', raw_text)` and indexed via GIN.
- **Dense Vector Search:** Native `vector(384)` indexed via HNSW cosine distance (`vector_cosine_ops`).

---

## 3. Operational Commands

### Running Ingestion via CLI
```powershell
# From backend directory with default settings:
cd backend
python -m app.cli ingest --dataset-path ../data/raw

# Run fast text-only ingestion (skip embeddings):
python -m app.cli ingest --dataset-path ../data/raw --skip-embeddings

# Force re-ingestion of already processed meetings:
python -m app.cli ingest --dataset-path ../data/raw --force

# Smoke test with first 5 meetings:
python -m app.cli ingest --dataset-path ../data/raw --limit 5 --skip-embeddings
```

### Running Ingestion via REST API
```http
POST /api/v1/ingestion/jobs?sync=true
Content-Type: application/json

{
  "force_reingest": false,
  "skip_embeddings": false,
  "limit_files": 10
}
```

```http
GET /api/v1/ingestion/jobs/{job_id}
GET /api/v1/ingestion/jobs
GET /api/v1/ingestion/stats
```
