# Phase 2 Ingestion & Indexing Report

**Project:** Catalist Meeting Intelligence Agent  
**Phase:** 02 — Dataset Discovery, Transcript Ingestion & Indexing  
**Status:** Completed & Accepted  
**Date:** 2026-11-23  
**Author:** Catalist Senior Implementation Architect  

---

## 1. Executive Summary

Phase 2 established a reliable, idempotent, resumable, and fault-tolerant ingestion pipeline that converts the AMI Meeting Corpus transcript archive into structured PostgreSQL 16 + pgvector storage.

All 138 meeting transcripts across 35 design teams were inventoried, validated, parsed, and indexed. Exact speaker speech, disfluencies, false starts, and timestamps have been preserved verbatim. Dense vector embeddings (384-dimensional `sentence-transformers/all-MiniLM-L6-v2`) and full-text search indexes (`tsvector` + GIN) are fully operational.

---

## 2. Dataset Discovery and Inventory

| Item | Value / Metric | Description |
|---|---|---|
| **Archive File** | `data/raw/Catalist_AI_Intern_Build_Test_Data.zip` | Supplied benchmark dataset archive |
| **Archive Size** | 1,515,873 bytes (~1.45 MB) | Validated within 50 MB safety ceiling |
| **Total Archive Entries** | 140 entries | 138 transcripts, 1 credits file, 1 questions file |
| **Transcript Files** | 138 `.txt` files | Individual AMI meeting transcripts |
| **Benchmark Questions** | 25 questions in `data/raw/questions.json` | Cross-meeting evaluation queries (`Q01` - `Q25`) |
| **Total Design Teams** | 35 teams | Teams `ES2002`–`ES2016`, `IS1000` series, `TS3001`–`TS3012` |
| **Standard 4-Meeting Teams**| 33 teams (132 meetings) | Series containing meetings `a`, `b`, `c`, and `d` |
| **3-Meeting Teams** | 2 teams (6 meetings) | `IS1002` (`b`, `c`, `d`), `IS1005` (`a`, `b`, `c`) |
| **Total Meeting Transcripts**| Exactly 138 meetings | 132 + 6 = 138 (matches original brief exactly) |
| **Corpus Word Count** | ~676,000 words | Real multi-party conversational speech |

---

## 3. Sample Meeting & Turn Verification

To verify that the parser preserves exact ground-truth speech without normalization, transcript `ES2002a.txt` was verified against its stored representation:

### Source Header (`ES2002a.txt`):
```text
Meeting: ES2002a
Team: ES2002
Meeting number: 1 (a) of the team's four meetings
Speakers: Speaker A, Speaker B, Speaker C, Speaker D
Times: turn start time from the start of the recording (HH:MM:SS)
Source: AMI Meeting Corpus, CC BY 4.0
```

### Turn 0 Verification:
- **Timestamp:** `00:00:50` (50 seconds)
- **Speaker:** `Speaker B`
- **End Time:** `00:01:06` (66 seconds, derived from Turn 1 start)
- **Verbatim Text:**
  ```text
  Okay. Right. Um well this is the kick-off meeting for our our project. Um and um this is just what we're gonna be doing over the next twenty five minutes. Um so first of all, just to kind of make sure that we all know each other, I'm Laura and I'm the project manager. Do you want to introduce yourself again?
  ```
- **Preservation Check:** "Um well this is the kick-off meeting for our our project" was preserved with exact repeated "our our", fillers "um", and contractions "gonna".
- **Turn 1 (Speaker D):** `00:01:06` -> `"Mm-hmm. Great."` (exact filler preserved).
- **Turn 2 (Speaker A):** `00:01:17` -> `"Hi, I'm David and I'm supposed to be an industrial designer."`

---

## 4. Key Architectural Implementations

1. **Safe Archive Service (`app/services/archive_service.py`):**
   Defends against Zip Slip directory traversal attacks by validating all entry paths against destination roots, checking extensions against an allowed whitelist (`.txt`, `.json`), enforcing uncompressed size limits, and rejecting symlinks.
2. **Deterministic Parser (`app/services/parser_service.py`):**
   Parses AMI transcript headers and turn utterances into typed Pydantic models (`ParsedMeeting`, `ParsedTurn`, `ParsedSpeaker`). Validates turn boundaries, maintains monotonic timestamp ordering, and flags anomalies.
3. **Local Embedding Service (`app/services/embedding_service.py`):**
   Singleton service loading `sentence-transformers/all-MiniLM-L6-v2` locally on CPU. Generates normalized 384-dimensional dense vectors in batches. Enforces `HF_HUB_OFFLINE=1` to guarantee instant offline execution without external network requests.
4. **PostgreSQL Full-Text Search:**
   Native `tsvector` maintained via PostgreSQL C-trigger `tsvector_update_trigger(search_vector, 'pg_catalog.english', raw_text)` and indexed with a GIN index.
5. **Database Models & Migration (`002_dataset_ingestion_schema.py`):**
   Establishes `teams`, `meetings`, `speakers`, `transcript_turns`, and `ingestion_jobs` tables with full referential integrity and cascading deletes.
6. **Ingestion Orchestration & Idempotency (`app/services/ingestion_service.py`):**
   Computes SHA-256 for each transcript file; skips unchanged meetings automatically; encapsulates each meeting in a transaction savepoint for strict fault isolation.
7. **CLI & API Interfaces (`app/cli.py`, `app/api/v1/endpoints/ingestion.py`):**
   Provides CLI commands (`python -m app.cli ingest`) and REST endpoints (`POST /api/v1/ingestion/jobs`, `GET /api/v1/ingestion/stats`).

---

## 5. Automated Test Results

| Test Module | Tests | Result | Execution Time | Description |
|---|---|---|---|---|
| `tests/test_archive.py` | 6 | **PASSED** | 0.05s | Path traversal, disallowed extensions, file count, and size limits |
| `tests/test_parser.py` | 13 | **PASSED** | 0.06s | Header parsing, turn boundaries, disfluency preservation, blank lines |
| `tests/test_embedding.py` | 3 | **PASSED** | 0.82s | Singleton lifecycle, 384d dimension check, empty-text handling |
| `tests/test_ingestion.py` | 5 | **PASSED** | 0.45s | Persistence, idempotency, re-ingestion, speaker scoping, fault isolation |
| `tests/test_ingestion_api.py` | 4 | **PASSED** | 0.28s | Ingestion job creation, progress retrieval, stats, 404 responses |
| `tests/test_config.py` | 4 | **PASSED** | 0.02s | Application configuration and environment validation |
| `tests/test_health.py` | 2 | **PASSED** | 0.03s | Health and root metadata endpoints |
| `tests/test_ready.py` | 2 | **PASSED** | 0.03s | Readiness probes and database failure isolation |
| `tests/test_middleware.py` | 5 | **PASSED** | 0.04s | Request ID propagation, sanitization, process timing |
| `tests/test_tracing.py` | 4 | **PASSED** | 0.03s | LangSmith safe disablement without credentials |
| **Total Backend Tests** | **48** | **ALL PASSED** | **21.75s** | Complete backend test suite |
| **Total Frontend Tests** | **8** | **ALL PASSED** | **15.69s** | Vitest UI and status component tests |

---

## 6. Phase Acceptance Checklist

- [x] Dataset path discovered and validated (`data/raw/Catalist_AI_Intern_Build_Test_Data.zip`).
- [x] Transcript files discovered without hardcoded machine paths.
- [x] Meeting metadata parsed correctly (meeting code, team code, sequence letter, speakers).
- [x] Speaker turns parsed with exact verbatim source text (preserving "um", "uh", repetitions).
- [x] Speaker identity strictly scoped to individual meetings (unique row per meeting).
- [x] Database migration works cleanly from scratch (`002_dataset_ingestion_schema`).
- [x] PostgreSQL pgvector extension enabled.
- [x] Turn dense embedding dimension validated at 384 (`sentence-transformers/all-MiniLM-L6-v2`).
- [x] Full-text search index operational (PostgreSQL `tsvector` + GIN).
- [x] Ingestion is idempotent (SHA-256 checks skip unchanged files in 0.02s).
- [x] Changed source files supported through controlled `--force` re-ingestion path.
- [x] Failed meetings can be retried without deleting other records.
- [x] One failed meeting does not roll back previously completed meetings (fault isolation verified).
- [x] Ingestion progress reports real counts (turns, words, meetings, files).
- [x] Complete test suite passes (48 backend tests + 8 frontend tests).
- [x] Documentation reflects actual implementation.
- [x] **No Phase 3 code (memory extraction, summarization, or answering agent) has been introduced.**

