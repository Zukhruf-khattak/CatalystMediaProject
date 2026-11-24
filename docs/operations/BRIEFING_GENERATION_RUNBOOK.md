# Pre-Meeting Briefing Generation Runbook

## 1. Overview and Operational Purpose

The **Briefing Service** (`app.services.briefing_service.py`) generates versioned pre-meeting intelligence briefings for teams preparing for upcoming meetings. This runbook details operational procedures for:
- Generating and regenerating team briefings via REST API and CLI.
- Inspecting briefing versions and validation reports.
- Troubleshooting coverage notices and validation warnings.
- Performing SQL audit checks on stored briefings.

---

## 2. CLI Usage & Common Commands

The Catalist CLI exposes the `brief` command for headless and automation workflows:

```bash
# 1. Generate default Team TS3012 pre-meeting briefing (before final meeting)
catalist brief

# 2. Generate briefing targeting a specific upcoming meeting
catalist brief --team TS3012 --before TS3012d

# 3. Force regeneration to create a new version
catalist brief --team TS3012 --regenerate

# 4. Save briefing directly to a Markdown file
catalist brief --team TS3012 --save docs/TS3012_PreMeeting_Brief.md

# 5. Output structured JSON payload
catalist brief --team TS3012 --format json
```

---

## 3. REST API Operations

### 3.1 Generate Briefing (`POST /api/v1/briefings/generate`)

```bash
curl -X POST http://localhost:8000/api/v1/briefings/generate \
  -H "Content-Type: application/json" \
  -d '{
    "team_code": "TS3012",
    "target_meeting_code": "TS3012d",
    "regenerate": true
  }' | jq '{title, version, validation_status, citations_count}'
```

### 3.2 Convenience TS3012 Endpoint (`GET /api/v1/briefings/ts3012`)

```bash
curl -X GET http://localhost:8000/api/v1/briefings/ts3012 | jq '{title, version, meetings_covered}'
```

### 3.3 Fetch Latest Briefing (`GET /api/v1/briefings/{team_code}/latest`)

```bash
curl -X GET http://localhost:8000/api/v1/briefings/TS3012/latest
```

### 3.4 List Historical Versions (`GET /api/v1/briefings/{team_code}/versions`)

```bash
curl -X GET http://localhost:8000/api/v1/briefings/TS3012/versions | jq '.briefings[] | {version, created_at, citations_count}'
```

### 3.5 Retrieve by Unique ID (`GET /api/v1/briefings/{id}`)

```bash
curl -X GET http://localhost:8000/api/v1/briefings/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

---

## 4. Investigating Validation Warnings & Gaps

### Data Coverage Notice: Missing Meetings
If Section 1 displays:
`> [!WARNING] Data Coverage Notice: Meeting TS3012b (stage 'b') is absent from the ingested corpus.`
- **Cause**: The team sequence has missing files in `data/raw/transcripts/` or ingestion was partial.
- **Action**: Check `meetings` table in PostgreSQL:
  ```sql
  SELECT m.meeting_code, m.sequence_letter, m.meeting_number 
  FROM meetings m 
  JOIN teams t ON m.team_id = t.id 
  WHERE t.team_code = 'TS3012' 
  ORDER BY m.meeting_number;
  ```

### Citation Validation Warnings
If `validation_status` is `WARNING`:
- Inspect `validation_errors` array in the JSON response or database record.
- Common causes:
  - Quotation contains $< 6$ words.
  - Quotation modified from raw transcript text.
  - Speaker label mismatch against turn record.
- **Remediation**: Run database verification query:
  ```sql
  SELECT t.turn_index, s.speaker_label, s.role, t.raw_text
  FROM transcript_turns t
  JOIN meetings m ON t.meeting_id = m.id
  LEFT JOIN speakers s ON t.speaker_id = s.id
  WHERE m.meeting_code = 'TS3012c'
    AND t.raw_text ILIKE '%rubber%';
  ```

---

## 5. Maintenance and Performance

- **Regeneration Cadence**: Trigger regeneration automatically whenever new meetings are ingested for a team via the ingestion job webhook.
- **Storage Profile**: Each briefing record averages ~8KB of Markdown and structured JSON. Storing 100 versions per team across 1,000 teams requires $< 1$ GB of PostgreSQL storage.
- **Latency**: Generating a briefing with citation validation on a 4-meeting team takes $< 150$ ms on standard CPU hardware.

