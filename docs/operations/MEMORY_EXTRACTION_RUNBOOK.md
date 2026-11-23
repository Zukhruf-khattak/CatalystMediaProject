# Memory Extraction & Retrieval Runbook

## 1. Overview

This runbook describes operations for extracting, searching, and managing temporal meeting memories using the Catalist CLI and REST API.

---

## 2. CLI Usage

The Catalist CLI provides subcommands to extract and query temporal memories.

### 2.1 Chronological Team Extraction
To extract temporal memories for an entire team series (meetings `a` -> `b` -> `c` -> `d`) preserving temporal links:

```bash
python -m app.cli extract-memory --team-code TS3006
```

### 2.2 Single Meeting Extraction
To extract memories for a specific meeting:

```bash
python -m app.cli extract-memory --meeting-code TS3006a
```

### 2.3 Force Re-Extraction (Idempotency Override)
By default, already completed meetings are skipped (`force=False`). To wipe prior memories for a meeting and re-extract:

```bash
python -m app.cli extract-memory --meeting-code TS3006a --force
```

### 2.4 Searching Memories via CLI
Search memories with multi-dimensional filtering:

```bash
# Search decisions for a specific team
python -m app.cli search-memory --team-code TS3006 --type DECISION

# Search active/current memories
python -m app.cli search-memory --team-code TS3006 --status current

# Lexical search on statements and quotations
python -m app.cli search-memory --query "kinetic battery" --limit 10
```

---

## 3. REST API Usage

### 3.1 Trigger Extraction
**Endpoint**: `POST /api/v1/memory/extract`

```json
{
  "team_code": "TS3006",
  "force": false,
  "extraction_version": "1.0.0"
}
```

Response (`202 Accepted`):
```json
{
  "id": "7b8e1a2f-4c5d-4e9b-8a12-9c3f4e5a6b7c",
  "team_id": "90b6585c-4c9c-41b7-b7ad-759bb1b49d20",
  "meeting_id": "f2cf1691-ff9e-490f-8652-3a8bf66b6a3c",
  "status": "COMPLETED",
  "started_at": "2026-11-23T14:30:00Z",
  "completed_at": "2026-11-23T14:30:15Z",
  "total_turns_analyzed": 542,
  "total_memories_extracted": 14,
  "total_memories_validated": 12,
  "total_memories_rejected": 2,
  "total_relationships_created": 3,
  "errors_json": [
    {
      "candidate": {"quote": "we should maybe do titanium"},
      "turn_index": 44,
      "reason": "Quotation has only 5 words; minimum required is 6."
    }
  ],
  "summary_json": {
    "meeting_code": "TS3006a",
    "team_code": "TS3006",
    "total_turns": 542,
    "validated": 12,
    "rejected": 2
  }
}
```

### 3.2 Search Memories
**Endpoint**: `GET /api/v1/memory/search?team_code=TS3006&status=current&limit=20`

Response:
```json
{
  "items": [
    {
      "id": "040406da-cc6b-48ca-8b5a-cfc098fa133e",
      "team_id": "90b6585c-4c9c-41b7-b7ad-759bb1b49d20",
      "meeting_id": "f2cf1691-ff9e-490f-8652-3a8bf66b6a3c",
      "turn_id": "43ffa2d3-f7c1-468d-bb72-d3284e48cfcf",
      "memory_type": "DECISION",
      "statement": "The team decided to use kinetic power instead of standard batteries.",
      "quote": "we are definitely going with kinetic power for this remote",
      "speaker_label": "Speaker B",
      "speaker_role": "Industrial Designer",
      "meeting_order": 2,
      "sequence_letter": "b",
      "status": "current",
      "confidence": 0.95,
      "extraction_version": "1.0.0",
      "metadata_json": {"topic": "power_source"},
      "outgoing_relationships": [
        {
          "id": "8f1a2b3c-...",
          "source_memory_id": "040406da-...",
          "target_memory_id": "11223344-...",
          "relationship_type": "supersedes",
          "rationale": "Decision in meeting b supersedes meeting a on topic 'power_source'.",
          "is_ambiguous": false,
          "confidence": 1.0,
          "created_at": "2026-11-23T14:30:10Z"
        }
      ],
      "incoming_relationships": []
    }
  ],
  "total_count": 1,
  "limit": 20,
  "offset": 0
}
```

---

## 4. Troubleshooting & Best Practices

1. **Rejection Spikes**: If `total_memories_rejected` is high, inspect `run.errors_json`. Common causes:
   - Modified/paraphrased quotations: LLM hallucinated words not in verbatim turn text.
   - Quotation < 6 words: Prompt instructs minimum 6 words.
   - Speaker label mismatch: LLM attributed turn to Speaker A when Speaker C uttered the turn.
2. **Ambiguous Relationships**: If team members use tentative language ("maybe we could think about..."), the relationship is marked with `is_ambiguous=True` and the prior decision remains `current`.
3. **Database Integrity**: Deleting a meeting automatically cascades deletions to its memories, relationships, and turns. Older historical memories are never deleted during normal operation.
