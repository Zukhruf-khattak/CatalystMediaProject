# Antigravity Prompt — Phase 2: Dataset Ingestion and Preprocessing

**Project:** Catalist Meeting Intelligence Agent  
**Phase:** 02 of 09  
**Mode:** Inspect first, implement incrementally, test, document  
**Primary outcome:** A reliable, resumable ingestion pipeline that converts the supplied meeting transcript archive into queryable PostgreSQL meeting and speaker-turn records, with local embeddings and search indexes.

---

## 1. Your role

Act as a senior Python backend engineer and data-ingestion engineer working inside the existing Catalist Meeting Intelligence Agent repository.

Implement this phase in the existing project. The Phase 1 technical specification is the authoritative architecture baseline. Inspect it and the current repository before making changes.

Do not redesign the system. Do not generate a new project beside the existing one. Preserve working code and follow the established folder structure, naming conventions, dependencies and database patterns.

## 2. Read these files first

Before editing anything, inspect:

1. `docs/` — especially the Phase 1 technical specification and database design.
2. `docs/prompts/README.md`.
3. `docker-compose.yml`.
4. `.env.example`.
5. `backend/pyproject.toml` or the existing dependency file.
6. Existing SQLAlchemy models, database session setup and Alembic migrations.
7. Existing FastAPI configuration and ingestion-related modules.
8. The supplied Catalist ZIP/archive and its actual location in the repository or workspace.
9. The supplied `questions.json` and at least two transcript files, if present.

Produce a short implementation assessment before coding:
- what already exists;
- what is missing;
- which files will be created or changed;
- any mismatch between the repository and the Phase 1 specification.

Then implement. Do not stop after the assessment unless a required input is genuinely unavailable.

## 3. Fixed architecture decisions

Use the decisions already locked in Phase 1:

- Python 3.12.
- FastAPI backend.
- PostgreSQL 16 with pgvector.
- SQLAlchemy 2.
- Alembic migrations.
- Pydantic v2.
- Local `sentence-transformers/all-MiniLM-L6-v2` embeddings (384 dimensions).
- PostgreSQL Full-Text Search for lexical retrieval.
- Docker Compose for local infrastructure.
- Pytest for backend tests.

The canonical evidence unit is one original speaker turn. Preserve exact transcript wording, speaker label, timestamp, meeting ID and turn order.

The original transcript is the source of truth. Do not rewrite, summarize, clean up or normalize stored source text.

## 4. Phase boundaries

### Implement in this phase

- Dataset/archive discovery and safe validation.
- Safe ZIP extraction, if the supplied dataset is archived.
- Transcript file discovery.
- Meeting metadata parsing.
- Speaker-turn parsing.
- Transcript and turn validation.
- Meeting, speaker and transcript-turn persistence.
- Source checksums and idempotent re-ingestion.
- Ingestion job status, errors and resumability.
- Local embedding generation and persistence.
- PostgreSQL full-text search indexing.
- Ingestion API endpoints and progress reporting.
- CLI/script for ingestion.
- Unit and integration tests.
- Documentation updates.

### Do not implement in this phase

- LLM-based memory extraction.
- Decision/action/disagreement extraction.
- Temporal memory reasoning.
- LangGraph research agent.
- Research answer generation.
- Citation answer generation or the final citation validator.
- TS3012 briefing generation.
- Full React product UI.

Keep the phase focused. Do not introduce Redis, Celery, a separate vector database, microservices or paid embedding APIs.

## 5. Dataset requirements

The supplied archive is expected to contain the Catalist meeting transcript subset and `questions.json`. The Phase 1 specification records 138 meetings, 35 teams and 25 benchmark questions. Verify these facts against the actual files rather than hardcoding them.

The parser must support the observed transcript structure, including metadata similar to:

```text
Meeting: ES2002a
Team: ES2002
Meeting number: 1 (a) of the team's four meetings
Speakers: Speaker A, Speaker B, Speaker C, Speaker D

00:00:50 Speaker B
Okay. Right. Um well this is the kick-off meeting...
```

Treat the example as a format illustration, not a fixed dataset value.

Important:
- Discover the real dataset path. Do not invent a path.
- Do not modify the supplied source files.
- Do not assume every transcript has identical metadata ordering.
- Handle blank lines and multi-line speaker turns.
- Preserve speaker labels exactly.
- Preserve the original timestamp string and, where useful, parse it into a numeric duration.
- Record parsing warnings and failures with the source filename and line context.
- Do not silently discard malformed content.

If the archive is not available in the workspace, implement the parser and tests using small synthetic fixtures, document the missing dataset, and clearly report that full-dataset ingestion has not been verified. Do not claim all 138 meetings were ingested.

## 6. Data model and persistence

Inspect existing models first. Reuse and extend them rather than creating duplicate tables.

The ingestion pipeline needs these core records:

### Team
- Stable internal ID.
- Unique team code.

### Meeting
- Stable internal ID.
- Unique meeting code.
- Team foreign key.
- Meeting suffix/letter where available.
- Sequence number where available.
- Source filename/path relative to configured dataset root.
- SHA-256 source checksum.
- Raw transcript text or an equivalent immutable source representation.
- Ingestion status.
- Created/updated timestamps.
- Parser version.

### Speaker
- Meeting-scoped speaker identity.
- Exact speaker label, such as `Speaker A`.
- Optional person name and role only if the transcript explicitly supplies them.
- Do not assume `Speaker A` in different meetings is the same person.

### TranscriptTurn
- Stable ID.
- Meeting foreign key.
- Speaker foreign key.
- Turn index.
- Original timestamp string.
- Optional parsed timestamp in seconds.
- Exact original turn text.
- 384-dimensional embedding, nullable until successfully generated.
- PostgreSQL `tsvector` or generated/search-vector strategy for full-text search.
- Unique constraint on `(meeting_id, turn_index)`.

### IngestionJob
- Job ID.
- Optional meeting ID.
- Status: pending, processing, completed or failed.
- Attempt count.
- Started/completed timestamps.
- Error message and useful failure context.
- Dataset/archive identifier or source reference.

Use appropriate foreign keys, unique constraints, indexes and transaction boundaries. Follow the existing migration conventions.

Do not add memory tables in this phase unless they already exist as part of the approved Phase 1 schema. Do not store derived LLM summaries as transcript content.

## 7. Parser implementation

Create a deterministic parser with small, testable functions.

Suggested responsibilities:
- `discover_transcript_files(...)`
- `parse_meeting_metadata(...)`
- `parse_speaker_roster(...)`
- `parse_turns(...)`
- `parse_transcript(...)`
- `validate_parsed_meeting(...)`

Adapt names to the existing codebase.

The parser output should be a typed Pydantic model, not an unstructured dictionary.

A parsed meeting should contain:
- meeting code;
- team code;
- sequence/suffix metadata where available;
- speaker roster;
- ordered turns;
- source filename;
- parser warnings.

Each turn should contain:
- turn index;
- speaker label;
- timestamp string;
- parsed timestamp seconds where possible;
- exact text.

Parsing requirements:
1. Identify turn boundaries from timestamp and speaker headers.
2. Associate all following transcript lines with the active turn until the next valid turn header.
3. Preserve line breaks and wording inside a turn.
4. Reject or flag turns with missing speaker labels or empty text.
5. Validate monotonic turn order where the format supports it; report anomalies instead of changing source timestamps.
6. Detect missing meeting/team metadata and produce explicit validation errors.
7. Avoid parsing ordinary transcript text as a new header unless it matches the full expected header pattern.
8. Make parser behavior deterministic and testable.

## 8. Archive safety

If ZIP extraction is required:
- Reject absolute paths.
- Reject `..` traversal paths.
- Reject symlinks or unsafe archive entries.
- Enforce a configurable maximum compressed archive size and extracted size.
- Enforce a maximum file count.
- Extract only allowed transcript/data file types.
- Do not execute archive contents.
- Do not overwrite arbitrary files outside the configured data directory.
- Log rejected entries safely.

Use a temporary extraction directory and only promote validated files into the configured dataset location.

## 9. Idempotency and resumability

The same archive must be safe to ingest more than once.

Implement:
- SHA-256 checksum per source transcript.
- Unique meeting code constraint.
- Unique `(meeting_id, turn_index)` constraint.
- A stable job status lifecycle.
- Skip unchanged completed meetings.
- Reprocess a changed transcript through a controlled transaction.
- Avoid duplicate speakers and turns.
- Persist failure status and error information.
- Allow retry of failed meetings.
- Commit work in bounded units, preferably per meeting, so one malformed file does not roll back all successful meetings.

Do not mark a meeting completed until its required records and configured embeddings are persisted successfully.

## 10. Local embedding generation

Use `sentence-transformers/all-MiniLM-L6-v2` locally.

Requirements:
- Model name configurable through environment variables.
- Embedding dimension fixed and validated at 384 for this model.
- Generate embeddings in batches, not one model initialization per turn.
- Load the model once per ingestion process/service lifecycle.
- Use CPU-compatible execution by default.
- Handle empty text safely.
- Store the embedding model identifier and version in configuration/metadata so a future model change can trigger re-embedding.
- Do not call a paid embedding API.
- Do not silently mix embeddings from different models or dimensions.
- If embedding generation fails for a turn, record the failure and do not falsely report that turn as embedded.

If local hardware makes full embedding generation slow, expose batch size and progress configuration. Do not weaken correctness to make the progress bar look faster.

## 11. PostgreSQL search indexing

Implement PostgreSQL Full-Text Search for transcript turns.

Requirements:
- Use a documented language configuration.
- Create the required GIN index.
- Ensure inserts/updates keep the search vector current, using either a generated column or a controlled application strategy.
- Add pgvector extension setup through the documented database initialization/migration process.
- Create the vector column with the correct 384 dimensions.
- Add a vector index only if supported and appropriate for the current PostgreSQL/pgvector version and measured dataset size.
- Document the chosen distance metric and index behavior.
- Ensure the database can be initialized from a clean Docker volume.

Do not implement the final hybrid retrieval ranking in this phase. The objective is to make both search indexes available and verifiable.

## 12. Ingestion service and API

Implement service-layer logic separately from FastAPI route handlers.

Suggested endpoints, aligned with the Phase 1 contract:

- `POST /api/v1/ingestion/jobs` — start ingestion for the configured dataset or an approved uploaded archive.
- `GET /api/v1/ingestion/jobs/{job_id}` — retrieve job status and counts.
- Add an endpoint for listing ingestion jobs if useful and consistent with the existing API.
- `GET /api/v1/health` — preserve the existing health contract.

The job response should include:
- job ID;
- status;
- total files discovered;
- meetings completed;
- meetings failed;
- meetings skipped;
- total turns parsed;
- total turns embedded;
- current meeting/file;
- start and completion timestamps;
- structured error summary.

Do not return full transcript bodies in job status responses.

If background execution is already established, use the existing approved mechanism. If not, implement a simple bounded background approach suitable for the local assessment and document its limitations. Do not add Redis/Celery.

Provide a CLI script such as:

```powershell
python -m app.scripts.ingest_dataset --dataset-path "<actual-path>"
```

Adapt the command to the existing repository and ensure it works from the documented working directory. Do not hardcode a Windows-only path.

## 13. Configuration

Add validated settings for:
- dataset root;
- allowed transcript extensions;
- archive limits;
- embedding model;
- embedding batch size;
- embedding device;
- parser version;
- ingestion batch/transaction behavior;
- database URL.

Update `.env.example` with placeholders and safe defaults. Never place real secrets in documentation or source control.

## 14. Observability and logging

Use the project's structured logging conventions.

Log:
- ingestion job started/completed/failed;
- file discovered/skipped/processed;
- meeting parse success/failure;
- turn count;
- embedding batch progress;
- database persistence failures;
- elapsed time per stage.

Include job ID, meeting code and source filename in relevant log context.

Do not log entire transcript bodies. Do not log credentials.

LangSmith tracing is part of the wider project architecture, but do not add unnecessary LLM tracing to deterministic ingestion. If LangSmith integration already exists, retain it without making ingestion depend on it.

## 15. Required tests

Create tests for at least the following.

### Parser unit tests
1. Parse a valid meeting header.
2. Parse a valid speaker roster.
3. Parse a valid timestamped turn.
4. Parse multiple turns.
5. Preserve multi-line turn text exactly.
6. Preserve speaker labels.
7. Handle blank lines.
8. Handle missing team metadata.
9. Handle malformed timestamp/header.
10. Handle empty turn text.
11. Detect out-of-order timestamps.
12. Ensure transcript text that resembles a header is not incorrectly split unless it matches the full header pattern.

### Archive safety tests
1. Reject `../` traversal entries.
2. Reject absolute paths.
3. Reject disallowed file types.
4. Enforce extraction limits.
5. Confirm valid archive extraction stays inside the configured directory.

### Persistence and idempotency tests
1. Persist team, meeting, speaker and turns.
2. Re-ingest unchanged source without duplicates.
3. Re-ingest changed source through the controlled update path.
4. Keep meeting-scoped speaker identity.
5. Roll back a failed meeting transaction.
6. Preserve already completed meetings when another meeting fails.
7. Retry a failed job.

### Embedding and index tests
1. Verify embedding dimension is 384.
2. Verify batch generation.
3. Verify empty text handling.
4. Verify embeddings persist and can be read.
5. Verify PostgreSQL full-text search returns a known fixture turn.
6. Verify pgvector extension and column configuration.

### API tests
1. Start an ingestion job.
2. Read job progress.
3. Read a failed job's error summary.
4. Confirm the health endpoint remains functional.
5. Validate response schemas.

Use test fixtures. Keep unit tests independent of external APIs. Integration tests may require a test PostgreSQL service and should be clearly marked.

## 16. Documentation deliverables

Update documentation as part of the implementation. Do not postpone it.

Create or update:

- `docs/04_DATA_INGESTION_PIPELINE.md`
  - pipeline stages;
  - parser format;
  - archive safety;
  - idempotency;
  - resumability;
  - failure handling;
  - operational commands.

- `docs/05_DATABASE_DESIGN.md`
  - actual implemented tables;
  - columns and types;
  - foreign keys;
  - indexes;
  - constraints;
  - migration instructions;
  - embedding dimension and FTS design.

- `docs/17_TESTING_STRATEGY.md`
  - test organization;
  - commands;
  - fixtures;
  - integration-test database requirements.

- `docs/diagrams/ingestion_pipeline.mmd`
  - Mermaid ingestion flow matching the implementation.

- `docs/prompts/README.md`
  - update Phase 2 status only after acceptance criteria pass.

- `README.md`
  - prerequisites;
  - environment setup;
  - PostgreSQL/Docker startup;
  - migrations;
  - dataset location configuration;
  - ingestion CLI/API usage;
  - test commands;
  - troubleshooting.

Documentation must describe what is actually implemented. Do not document planned features as completed.

## 17. Implementation quality requirements

- Follow modular architecture and existing naming conventions.
- Use type hints.
- Use Pydantic schemas at data boundaries.
- Keep parsing, persistence, embedding and API responsibilities separate.
- Use SQLAlchemy 2 patterns already adopted by the project.
- Use Alembic migrations; do not rely on manual database edits.
- Use transactions and database constraints for integrity.
- Keep functions small and testable.
- Avoid unnecessary dependencies.
- Avoid placeholder implementations and fake progress.
- Avoid broad exception swallowing.
- Provide actionable error messages.
- Do not claim a test passed unless it was executed.
- Do not fabricate ingestion counts.
- Do not silently change Phase 1 architecture decisions.

## 18. Execution order

Implement in this order:

1. Inspect repository and dataset.
2. Report implementation assessment and exact files to change.
3. Confirm database extension and migration setup.
4. Implement typed parser and parser fixtures.
5. Implement archive validation/extraction if needed.
6. Implement SQLAlchemy models and Alembic migration.
7. Implement ingestion service and idempotency.
8. Implement local embedding service and persistence.
9. Implement PostgreSQL FTS/vector configuration.
10. Implement API and CLI.
11. Add unit and integration tests.
12. Run formatting, linting if configured, migrations and tests.
13. Run a small fixture ingestion.
14. Run full supplied dataset ingestion if the archive is available.
15. Verify counts and sample records against source files.
16. Update documentation and prompt index.
17. Provide a completion report.

Do not jump ahead to Phase 3.

## 19. Acceptance criteria

Phase 2 is complete only when the following are demonstrated:

- [ ] Dataset path was discovered and recorded, or its absence was explicitly reported.
- [ ] Transcript files are discovered without hardcoded machine-specific paths.
- [ ] Meeting metadata is parsed correctly.
- [ ] Speaker turns are parsed with exact source text.
- [ ] Speaker identity is scoped to a meeting.
- [ ] Database migration works from a clean database.
- [ ] PostgreSQL pgvector extension is enabled.
- [ ] Turn embedding dimension is 384.
- [ ] Full-text search index is operational.
- [ ] Ingestion is idempotent.
- [ ] Changed source files are handled through a controlled re-ingestion path.
- [ ] Failed meetings can be retried.
- [ ] One failed meeting does not erase successful meeting imports.
- [ ] Ingestion progress reports real counts.
- [ ] Parser, archive, persistence, embedding and API tests have been run.
- [ ] Documentation reflects the actual implementation.
- [ ] No memory extraction or research agent code has been prematurely introduced.

For the supplied complete dataset, verify the observed expected count of 138 meetings and 35 teams against the actual archive. If the supplied files differ, report the actual counts and investigate; do not force the database to match expected numbers.

## 20. Final response required from Antigravity

At completion, report:

1. Summary of what was implemented.
2. Exact files created and modified.
3. Database migration name and how to run it.
4. Exact ingestion command.
5. Dataset location actually used.
6. Actual meetings, teams, speakers, turns and embeddings processed.
7. Skipped and failed file counts with reasons.
8. Tests executed and their real results.
9. Sample meeting and turn verified against the original file.
10. Known limitations or unfinished work.
11. Documentation updated.
12. Confirmation that Phase 3 has not been started.

If any acceptance criterion fails, state it explicitly and identify the blocker. Do not mark Phase 2 complete until the evidence supports that claim.
