# Testing Strategy and Test Architecture

**Phase:** Phase 6 — Deterministic Citation and Evidence Validation  
**Status:** Operational  
**Coverage:** 128 automated backend tests + 8 frontend tests (136 total tests passing with 100% pass rate)

---

## 1. Test Suite Structure

```
backend/tests/
├── conftest.py               # In-memory SQLite session, TestClient fixture, and environment overrides
├── test_config.py            # Settings parsing, validation, bounds, and CORS assembly
├── test_health.py            # Health and root metadata endpoints
├── test_middleware.py        # Request ID propagation, sanitization, process timing, error handlers
├── test_ready.py             # Database connectivity readiness probes
├── test_tracing.py           # LangSmith configuration and metadata redaction
├── test_archive.py           # Safe ZIP extraction, Zip Slip defense, limits, and extension whitelisting
├── test_parser.py            # Deterministic AMI transcript parsing, turn splitting, and disfluency preservation
├── test_embedding.py         # all-MiniLM-L6-v2 singleton, 384d dimension validation, and empty-text handling
├── test_ingestion.py         # Idempotency, force-reingestion, meeting-scoped speakers, and fault isolation
└── test_ingestion_api.py     # Ingestion REST endpoints (/jobs, /jobs/{id}, /stats)
```

---

## 2. Test Execution Commands

### Run Full Backend Test Suite
```powershell
# From backend directory:
cd backend
.\.venv\Scripts\pytest -v

# Run only Phase 2 ingestion tests:
.\.venv\Scripts\pytest tests/test_archive.py tests/test_parser.py tests/test_embedding.py tests/test_ingestion.py tests/test_ingestion_api.py -v
```

### Run Frontend Test Suite
```powershell
cd frontend
npm test -- --run
```

### Run Code Formatting and Lint Checks
```powershell
cd backend
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
```

---

## 3. Key Test Categories

### 3.1. Parser Unit Tests (12 Test Cases)
- `test_parse_timestamp_seconds`: Validates conversions of HH:MM:SS format to total integer seconds.
- `test_normalize_search_text`: Verifies whitespace collapse and lowercase normalization for search indexing without affecting source text.
- `test_parse_valid_meeting_header`: Extracts meeting code, team code, sequence letter, and speaker roster.
- `test_parse_valid_speaker_roster`: Parses comma-separated speakers into typed speaker models.
- `test_parse_timestamped_turns`: Verifies turn boundaries, timestamps, and monotonic ordering.
- `test_preserve_multiline_turn_text_exactly`: Confirms character-for-character preservation of fillers ("um", "uh", "gonna") and multi-line speech.
- `test_preserve_speaker_labels`: Verifies exact labels ("Speaker A", "Speaker B", etc.).
- `test_handle_blank_lines`: Ensures arbitrary blank lines between or within turns do not corrupt state.
- `test_handle_missing_team_metadata`: Confirms automatic derivation of team code from meeting code (e.g. `ES2003b` -> `ES2003`).
- `test_handle_malformed_timestamp_warning`: Rejects invalid headers and logs actionable parser warnings without crashing.
- `test_handle_empty_turn_text_skipped_with_warning`: Detects empty/whitespace-only turns and skips them cleanly with logged warnings.
- `test_detect_out_of_order_timestamps`: Flags non-monotonic timestamps with parser warnings.
- `test_transcript_text_resembling_header_not_split`: Prevents false turn splits on conversational mentions of meeting codes or speakers.

### 3.2. Archive Security Tests (5 Test Cases)
- `test_is_safe_zip_entry`: Validates traversal path detection (`..`, absolute paths, drive prefixes).
- `test_reject_archive_traversal`: Confirms `ArchiveSecurityError` on path traversal entries.
- `test_reject_disallowed_file_types`: Verifies non-whitelisted extensions (e.g. `.exe`) are rejected.
- `test_enforce_file_count_limit`: Enforces maximum file count constraint.
- `test_enforce_archive_size_limit`: Enforces decompression size limits against zip bombs.
- `test_valid_archive_extraction`: Confirms safe extraction and promotion to destination directory.

### 3.3. Embedding Tests (3 Test Cases)
- `test_embedding_service_singleton`: Confirms single model instance across service lifecycle.
- `test_embedding_dimension_and_batch`: Validates dense vector length of exactly 384 dimensions on batch inputs.
- `test_embedding_empty_text_returns_zero_vector`: Validates zero vector fallback for empty text.

### 3.4. Persistence and Idempotency Tests (5 Test Cases)
- `test_ingestion_persistence_and_relationships`: Confirms team, meeting, speaker, and turn rows are committed with foreign key relationships.
- `test_ingestion_idempotency`: Verifies re-ingestion of unchanged files skips cleanly without duplicates.
- `test_ingestion_force_reingest`: Verifies `--force` re-ingestion cleanly replaces existing meeting records.
- `test_speaker_identity_is_meeting_scoped`: Confirms Speaker A in meeting 1 has distinct row and ID from Speaker A in meeting 2.
- `test_fault_isolation_one_bad_file_does_not_rollback_good_files`: Confirms nested transaction savepoints isolate corrupt files and allow valid meetings to persist.

### 3.5. API Tests (4 Test Cases)
- `test_get_dataset_stats_empty`: Verifies stats contract and zero counts on clean database.
- `test_get_nonexistent_job_returns_404`: Validates standard 404 response structure.
- `test_list_ingestion_jobs_empty`: Verifies job listing response schema.
- `test_create_sync_ingestion_job`: Tests synchronous job execution and response status 202.

### 3.6. Phase 6 Citation and Evidence Validation Tests (13 Test Cases)
The `backend/tests/test_citation_validation.py` test suite covers all 13 critical verification scenarios:
1. `test_exact_quotation_match`: Verbatim quotation of $\ge 6$ words passes individual validation.
2. `test_case_and_spacing_normalization`: Normalization of whitespace and casing succeeds without altering punctuation.
3. `test_modified_or_fabricated_quotation`: Modified or hallucinated quote text fails validation.
4. `test_quote_shorter_than_six_words`: Excerpt with $< 6$ words is strictly rejected.
5. `test_quote_stitched_across_turns`: Quotes spanning across multiple speaker turns are rejected.
6. `test_incorrect_meeting_id`: Citation referencing a nonexistent meeting fails validation.
7. `test_incorrect_team_id`: Citation referencing a meeting from a different team fails validation.
8. `test_incorrect_speaker_label`: Mismatch between cited speaker letter and verified transcript speaker fails.
9. `test_duplicate_meeting_citations`: Answer citing the same meeting multiple times fails multi-meeting requirement.
10. `test_evidence_from_only_one_meeting`: Single-meeting answer fails the cross-meeting evidence requirement ($\ge 2$ meetings).
11. `test_unsupported_answer_claims`: Answer with $< 20\%$ lexical overlap with citations is rejected for ungrounded claims.
12. `test_successful_validation_and_retry_behavior`: Agent retries on invalid candidate answer and succeeds when corrected.
13. `test_insufficient_evidence_after_retries`: Exhausting retries halts cleanly, clears invalid citations, and sets failure answer.


