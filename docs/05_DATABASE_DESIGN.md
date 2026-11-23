# Database Design and Schema Specification

**Engine:** PostgreSQL 16 with pgvector extension  
**ORM:** SQLAlchemy 2.0  
**Migration Tool:** Alembic  
**Current Revision:** `002_dataset_ingestion_schema`

---

## 1. Entity-Relationship Architecture

```
┌──────────────────┐
│      teams       │
├──────────────────┤
│ id (PK, UUID)    │◄────────┐
│ team_code (UQ)   │         │
│ created_at       │         │
│ updated_at       │         │
└──────────────────┘         │
                             │ (1:N)
┌──────────────────┐         │
│     meetings     │         │
├──────────────────┤         │
│ id (PK, UUID)    │         │
│ team_id (FK)     ├─────────┘
│ meeting_code(UQ) │◄────────┐
│ meeting_number   │         │
│ sequence_letter  │         │
│ total_turns      │         │
│ word_count       │         │
│ duration_seconds │         │ (1:N)
│ source_filename  │         │
│ source_sha256    │         │
│ status           │         │
│ raw_text (Text)  │         │
│ parser_version   │         │
│ created_at       │         │
│ updated_at       │         │
└──────────────────┘         │
       ▲                     │
       │ (1:N)               │
┌──────┴───────────┐         │
│     speakers     │         │
├──────────────────┤         │
│ id (PK, UUID)    │◄──┐     │
│ meeting_id (FK)  │   │     │
│ speaker_label    │   │     │
│ speaker_letter   │   │     │
│ role (nullable)  │   │     │
│ created_at       │   │     │
│ updated_at       │   │     │
└──────────────────┘   │     │
                       │     │
┌──────────────────────┴─────┴─────┐
│         transcript_turns         │
├──────────────────────────────────┤
│ id (PK, UUID)                    │
│ meeting_id (FK)                  │
│ speaker_id (FK)                  │
│ turn_index (INT)                 │
│ start_time_str (VARCHAR(16))     │
│ start_time_seconds (INT)         │
│ end_time_seconds (INT, nullable) │
│ raw_text (TEXT, immutable)       │
│ normalized_text (TEXT)           │
│ search_vector (TSVECTOR, GIN)    │
│ embedding (VECTOR(384), HNSW)    │
│ created_at                       │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│         ingestion_jobs           │
├──────────────────────────────────┤
│ id (PK, UUID)                    │
│ status (VARCHAR(32))             │
│ started_at (TIMESTAMP)           │
│ completed_at (TIMESTAMP)         │
│ total_files (INT)                │
│ completed_meetings (INT)         │
│ failed_meetings (INT)            │
│ skipped_meetings (INT)           │
│ total_turns (INT)                │
│ total_words (INT)                │
│ embedded_turns (INT)             │
│ current_file (VARCHAR(255))      │
│ errors_json (JSON)               │
│ summary_json (JSON)              │
└──────────────────────────────────┘
```

---

## 2. Table Specifications

### 2.1. `teams`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Stable internal UUID |
| `team_code` | `VARCHAR(32)` | `UNIQUE`, `NOT NULL`, `INDEX` | Unique team code (e.g. `ES2002`, `TS3012`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record modification timestamp |

### 2.2. `meetings`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Stable internal UUID |
| `team_id` | `UUID` | `NOT NULL`, `FK(teams.id ON DELETE CASCADE)`, `INDEX` | Owning team reference |
| `meeting_code` | `VARCHAR(32)` | `UNIQUE`, `NOT NULL`, `INDEX` | Unique meeting code (e.g. `ES2002a`) |
| `meeting_number`| `SMALLINT` | `NULLABLE` | Meeting index in series (1-4) |
| `sequence_letter`| `VARCHAR(4)`| `NULLABLE` | Letter code (`a`, `b`, `c`, `d`) |
| `total_turns` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Total turns in meeting |
| `word_count` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Total word count |
| `duration_seconds`| `FLOAT` | `NULLABLE` | Approximate duration in seconds |
| `source_filename` | `VARCHAR(255)`| `NOT NULL` | Original filename (e.g. `ES2002a.txt`) |
| `source_sha256` | `VARCHAR(64)` | `NOT NULL`, `INDEX` | SHA-256 hash of original file |
| `status` | `VARCHAR(32)` | `NOT NULL`, `DEFAULT 'INGESTED'` | Ingestion status tag |
| `raw_text` | `TEXT` | `NOT NULL` | Verbatim raw transcript text |
| `parser_version` | `VARCHAR(32)` | `NOT NULL`, `DEFAULT '1.0.0'` | Engine parser version |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record modification timestamp |

### 2.3. `speakers`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Stable internal UUID |
| `meeting_id` | `UUID` | `NOT NULL`, `FK(meetings.id ON DELETE CASCADE)`, `INDEX` | Owning meeting reference |
| `speaker_label`| `VARCHAR(32)`| `NOT NULL` | Exact label (e.g. `Speaker A`) |
| `speaker_letter`| `VARCHAR(8)` | `NOT NULL` | Single letter (`A`, `B`, `C`, `D`) |
| `role` | `VARCHAR(64)`| `NULLABLE` | Optional role if stated (e.g. `Project Manager`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record modification timestamp |
- **Table Constraint:** `UNIQUE (meeting_id, speaker_label)`

### 2.4. `transcript_turns`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Stable internal UUID |
| `meeting_id` | `UUID` | `NOT NULL`, `FK(meetings.id ON DELETE CASCADE)`, `INDEX` | Owning meeting reference |
| `speaker_id` | `UUID` | `NOT NULL`, `FK(speakers.id ON DELETE CASCADE)`, `INDEX` | Turn speaker reference |
| `turn_index` | `INTEGER` | `NOT NULL` | Monotonic 0-based turn index |
| `start_time_str`| `VARCHAR(16)`| `NOT NULL` | Original timestamp string (e.g. `00:00:50`) |
| `start_time_seconds`| `INTEGER`| `NOT NULL` | Turn start time in seconds |
| `end_time_seconds`| `INTEGER` | `NULLABLE` | Turn end time in seconds |
| `raw_text` | `TEXT` | `NOT NULL` | Verbatim ground-truth utterance |
| `normalized_text`| `TEXT` | `NOT NULL` | Lowercase/normalized text for lexical search |
| `search_vector`| `TSVECTOR` | `NULLABLE` | PostgreSQL tsvector for FTS |
| `embedding` | `VECTOR(384)`| `NULLABLE` | 384-dimensional dense vector |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |
- **Table Constraint:** `UNIQUE (meeting_id, turn_index)`
- **Composite Index:** `idx_turns_meeting_index (meeting_id, turn_index)`

### 2.5. `ingestion_jobs`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Unique job UUID |
| `status` | `VARCHAR(32)` | `NOT NULL`, `DEFAULT 'PENDING'` | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `PARTIAL` |
| `started_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Job launch time |
| `completed_at` | `TIMESTAMPTZ` | `NULLABLE` | Job completion time |
| `total_files` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Total files identified |
| `completed_meetings`| `INTEGER`| `NOT NULL`, `DEFAULT 0` | Successfully ingested count |
| `failed_meetings`| `INTEGER` | `NOT NULL`, `DEFAULT 0` | Failed ingestion count |
| `skipped_meetings`| `INTEGER`| `NOT NULL`, `DEFAULT 0` | Unchanged skipped count |
| `total_turns` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Total turns stored |
| `total_words` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Total words parsed |
| `embedded_turns`| `INTEGER` | `NOT NULL`, `DEFAULT 0` | Total turns with dense vectors |
| `current_file` | `VARCHAR(255)`| `NULLABLE` | Currently active file |
| `errors_json` | `JSON` | `NOT NULL`, `DEFAULT '[]'` | Error records with filename and trace |
| `summary_json`| `JSON` | `NOT NULL`, `DEFAULT '{}'` | Metadata and elapsed time metrics |

---

## 3. Indexes and Performance Strategy

1. **Full-Text Search GIN Index:**
   ```sql
   CREATE INDEX idx_turns_search_vector ON transcript_turns USING gin(search_vector);
   ```
   Maintained automatically via PostgreSQL C-trigger:
   ```sql
   CREATE TRIGGER trg_turns_search_vector_update
   BEFORE INSERT OR UPDATE ON transcript_turns
   FOR EACH ROW EXECUTE FUNCTION
   tsvector_update_trigger(search_vector, 'pg_catalog.english', raw_text);
   ```
2. **Dense Vector HNSW Index:**
   ```sql
   CREATE INDEX idx_turns_embedding_hnsw ON transcript_turns USING hnsw (embedding vector_cosine_ops);
   ```
   Supports fast approximate nearest neighbor (ANN) cosine similarity search for 384-dimensional vectors.
3. **Cross-Dialect Test Compatibility:**
   `CrossDialectVector` and `CrossDialectTSVector` custom types automatically map to PostgreSQL native `vector(384)` and `tsvector` in production, while falling back to standard `Text` on SQLite, allowing automated test suites to run completely in-memory in under 1 second.

