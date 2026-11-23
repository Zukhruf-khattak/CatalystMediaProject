# Retrieval Operations & CLI Runbook

## 1. Overview

This runbook guides operators and engineers in using the hybrid retrieval system via the Catalist CLI and REST API.

---

## 2. CLI Retrieval Operations

The `catalist retrieve` command executes query processing, keyword search, dense vector retrieval, and Reciprocal Rank Fusion.

### 2.1 Standard Hybrid Search
```bash
python -m app.cli retrieve --query "Team TS3006 planned an LCD screen and speech recognition"
```

Output:
```text
================================================================================
QUERY: Team TS3006 planned an LCD screen and speech recognition
EXTRACTED: Team=TS3006 | Topics=['lcd', 'screen', 'speech recognition'] | Intent=None
METHOD: hybrid | TOTAL TURNS: 10
CROSS-MEETING EVIDENCE: {'ts3006a': 4, 'ts3006c': 5, 'ts3006d': 1}
================================================================================

--- RETRIEVED TRANSCRIPT SEGMENTS ---
[1] ts3006a (Turn 24) | Speaker A (Project Manager) at 00:04:15 | Score: 0.03226
    "We have agreed to incorporate both an LCD screen and speech recognition."
--------------------------------------------------------------------------------
[2] ts3006c (Turn 89) | Speaker B (Industrial Designer) at 00:15:30 | Score: 0.03175
    "Due to budget cuts we must drop speech recognition and keep the LCD screen."
--------------------------------------------------------------------------------

--- RELATED TEMPORAL MEMORIES ---
[1] ts3006c | DECISION | Status: current | Links: supersedes->7b8e1a2f
    Statement: Team dropped speech recognition and kept LCD display.
    Quote:     "we must drop speech recognition and keep the LCD screen"
--------------------------------------------------------------------------------
```

### 2.2 Compare Keyword-Only vs Vector-Only
```bash
# Keyword-only channel
python -m app.cli retrieve --query "titanium casing" --team-code TS3006 --method keyword

# Vector-only channel
python -m app.cli retrieve --query "titanium casing" --team-code TS3006 --method vector
```

---

## 3. REST API Operations

### 3.1 Inspect Query Entity Extraction
**Endpoint**: `POST /api/v1/retrieval/process-query`

Request:
```json
{
  "query": "Team ES2003 leaned towards one material for the case and then switched to another."
}
```

Response:
```json
{
  "raw_query": "Team ES2003 leaned towards one material for the case and then switched to another.",
  "cleaned_keyword_query": "material case switched",
  "extracted_team": "ES2003",
  "extracted_meetings": [],
  "extracted_speakers": [],
  "extracted_topics": ["material", "case"],
  "temporal_intent": "change"
}
```

### 3.2 Execute Hybrid Search
**Endpoint**: `POST /api/v1/retrieval/search`

Request:
```json
{
  "query": "Team TS3006 planned an LCD screen and speech recognition",
  "team_code": "TS3006",
  "method": "hybrid",
  "limit": 10,
  "rrf_k": 60,
  "weight_keyword": 1.0,
  "weight_vector": 1.0,
  "include_temporal_memories": true
}
```

---

## 4. Tuning & Configuration Guidelines

1. **RRF Constant $k$ (default 60)**:
   - Decreasing $k$ (e.g. $k=20$) increases the relative reward for appearing at rank 1 or 2.
   - Increasing $k$ (e.g. $k=100$) makes rank differences smoother across large candidate sets.
2. **Channel Weighting**:
   - For exact part numbers, model codes, or technical jargon: set `weight_keyword=1.5, weight_vector=1.0`.
   - For exploratory or conceptually phrased queries: set `weight_keyword=0.8, weight_vector=1.2`.
3. **Multi-Meeting Verification**:
   - Check `cross_meeting_summary` in the response. If only one meeting is present for a multi-meeting question, inspect `temporal_memories` for outgoing relationship links to adjacent meetings in the series.

