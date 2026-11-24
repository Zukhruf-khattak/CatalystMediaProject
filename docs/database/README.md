# Database Setup & Migration Guide

**Project**: Catalist Meeting Intelligence Agent  
**Dialects Supported**: PostgreSQL 16 (+ `pgvector`) & SQLite (local development file DB)  
**ORM**: SQLAlchemy 2.x  
**Migration Tool**: Alembic  

---

## 1. Supported Database Engines

### PostgreSQL 16 with pgvector (Production / Docker Compose)
- **Extension**: `pgvector` (vector cosine distance `<=>`, inner product `<#>`, Euclidean `<->`)
- **Driver**: `psycopg` (v3) via SQLAlchemy (`postgresql+psycopg://catalist_user:catalist_password@localhost:5432/catalist_db`)
- **Full-Text Search**: Native PostgreSQL `tsvector` with `to_tsvector('english', raw_text)` and GIN indexes.

### SQLite 3 with FTS5 (Local File Development)
- **Database Path**: `data/processed/catalist.db` (`sqlite:///data/processed/catalist.db`)
- **Full-Text Search**: FTS5 virtual tables with Porter stemming.
- **Vector Storage**: IEEE 754 float32 BLOB vectors with cosine similarity computed via NumPy/Python.

---

## 2. Master Migration Sequence

| Migration ID | File Name | Description | Key Tables / Objects |
| :--- | :--- | :--- | :--- |
| **001** | `001_initial_pgvector.py` | Baseline pgvector extension initialization | `CREATE EXTENSION IF NOT EXISTS vector;` |
| **002** | `002_dataset_ingestion_schema.py` | Core transcript and metadata storage | `teams`, `meetings`, `speakers`, `transcript_turns`, `ingestion_jobs` |
| **003** | `003_temporal_memory_schema.py` | Persistent temporal memory & lineage graph | `memories`, `memory_relationships`, `memory_extraction_runs` |
| **004** | `004_agent_session_schema.py` | LangGraph agent persistence & checkpointing | `agent_sessions`, `agent_checkpoints` |
| **005** | `005_briefing_schema.py` | Pre-meeting executive briefings & versions | `briefings` |

---

## 3. Relational Schema Overview

```
 [Team] 1 ──── * [Meeting] 1 ──── * [TranscriptTurn] (with dense vector embedding)
                     │                      │
                     ▼                      ▼
                 [Speaker] 1 ──── * [TemporalMemory] 1 ──── * [MemoryRelationship]
                                            │
                                            ▼
                                   [PreMeetingBriefing]
```

### Table Details:
1. **`teams`**:
   - `id` (UUID, PK), `team_code` (VARCHAR, Unique, e.g. "TS3006"), `project_name` (VARCHAR).
2. **`meetings`**:
   - `id` (UUID, PK), `team_id` (FK -> teams.id), `meeting_code` (VARCHAR, Unique, e.g. "TS3006d"), `meeting_stage` (VARCHAR, "a", "b", "c", "d"), `meeting_order` (INT), `has_transcript` (BOOLEAN).
3. **`speakers`**:
   - `id` (UUID, PK), `meeting_id` (FK -> meetings.id), `speaker_label` (VARCHAR, "Speaker A", "B", "C", "D"), `speaker_role` (VARCHAR, "Project Manager", "Industrial Designer", etc.).
4. **`transcript_turns`**:
   - `id` (UUID, PK), `meeting_id` (FK -> meetings.id), `speaker_id` (FK -> speakers.id), `turn_index` (INT), `start_time` (FLOAT), `end_time` (FLOAT), `raw_text` (TEXT), `word_count` (INT), `embedding` (VECTOR(384) / BLOB).
5. **`memories`**:
   - `id` (UUID, PK), `team_id` (FK -> teams.id), `meeting_id` (FK -> meetings.id), `turn_id` (FK -> transcript_turns.id), `memory_type` (ENUM: decision, action, preference, disagreement), `statement` (TEXT), `supporting_quote` (TEXT), `status` (ENUM: current, superseded, open, resolved, rejected), `confidence` (FLOAT), `version` (INT).
6. **`memory_relationships`**:
   - `id` (UUID, PK), `source_memory_id` (FK -> memories.id), `target_memory_id` (FK -> memories.id), `relationship_type` (ENUM: updates, contradicts, supports).
7. **`briefings`**:
   - `id` (UUID, PK), `team_id` (FK -> teams.id), `target_meeting_id` (FK -> meetings.id), `version` (INT), `content_markdown` (TEXT), `citations_count` (INT), `is_valid` (BOOLEAN).
8. **`agent_sessions`**:
   - `id` (UUID, PK), `created_at` (TIMESTAMP), `query` (TEXT), `final_response` (TEXT), `validation_status` (VARCHAR).

---

## 4. Running Migrations Locally

```bash
# From backend directory with active virtualenv:
cd backend

# Apply all migrations to the latest revision:
alembic upgrade head

# Rollback one migration:
alembic downgrade -1

# Show current migration revision:
alembic current

# Show migration history:
alembic history --verbose
```
