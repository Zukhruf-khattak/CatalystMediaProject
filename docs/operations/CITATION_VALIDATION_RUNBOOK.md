# Citation Validation Runbook

## 1. Overview and Operational Role

The **Citation Validation Service** (`app.services.citation_validation_service.py`) acts as the deterministic quality assurance gate for all agent responses. This runbook documents operational procedures for:
1. Understanding validation failure modes.
2. Investigating and debugging citation rejections.
3. Troubleshooting quotation normalization issues.
4. Performing database audit checks on stored turns and citations.

---

## 2. Validation Error Taxonomy

When an answer or citation fails validation, the service returns structured error descriptions in `validation_errors`. The primary failure classes and root causes are:

| Error Pattern | Root Cause | Remediation |
|---|---|---|
| `Quotation was not found verbatim in referenced speaker turn` | Hallucination, paraphrase, or quote altered by LLM. | Ensure extraction extracts literal substring from `TranscriptTurn.raw_text`. |
| `Quotation was not found verbatim in any turn of meeting` | Quoting a turn from another meeting or hallucinated text. | Verify `meeting_code` and turn ID reference accuracy. |
| `Quotation contains N words; Catalist requirement is at least 6 words` | Excerpt is shorter than 6 whitespace-separated words. | Extract a longer contiguous sentence fragment ($\ge 6$ words). |
| `Turn ID belongs to a different meeting` | Citation references `turn_id` from meeting X but states `meeting_id` Y. | Ensure retrieved turn metadata retains proper meeting attribution. |
| `Meeting ... belongs to team X, not expected team Y` | Cross-team contamination in multi-tenant or multi-team query. | Check `team_code` filter in retrieval planning and query processor. |
| `Speaker label ... does not match turn speaker ...` | LLM misattributed the speaker letter (e.g. Speaker C instead of B). | Bind speaker label directly from `Speaker.speaker_label`. |
| `Claimed speaker role ... does not match transcript speaker role` | Role attributed to speaker is unverified by meeting metadata. | Omit speaker role unless explicitly verified in `Speaker.role`. |
| `Answer contains N sentences; Catalist requirement is 1 to 3 plain sentences` | Answer exceeds 3 sentences or is empty. | Prompt LLM strictly for 1-3 sentences or invoke deterministic fallback. |
| `Answer has N citations; Catalist requirement is 1 to 3 citations` | 0 citations or > 3 citations supplied. | Enforce citation bounds in `_extract_citations`. |
| `Answer cites 1 distinct meeting(s); Catalist requirement is ... at least 2 meetings` | Both citations come from the same meeting (e.g. `TS3006a` and `TS3006a`). | Enforce distinct meeting selection across team meetings. |
| `Answer contains unsubstantiated claims not backed by citation quotations` | Answer asserts facts completely unmentioned in citations (< 20% overlap). | Ensure answer claims directly mirror the cited speaker turns. |

---

## 3. Debugging Validation Failures

### 3.1 Inspecting via REST API

Execute an agent query with session inspection enabled:

```bash
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What casing material did Team ES2003 switch from and to?",
    "team_code": "ES2003"
  }' | jq '{answer, validation_status, validation_errors, supporting_meetings}'
```

Expected healthy output:
```json
{
  "answer": "Team ES2003 initially leaned towards a double curved rubber case in ES2003b. In ES2003d, they switched to standard plastic because rubber moulding exceeded the cost budget.",
  "validation_status": "PASSED",
  "validation_errors": [],
  "supporting_meetings": ["es2003b", "es2003d"]
}
```

### 3.2 Inspecting via Catalist CLI

```bash
catalist ask "What casing material did Team ES2003 switch from and to?" --team ES2003
```

Check the CLI output logs for `[citation_validation]` step logs and error traces.

### 3.3 Database Audit Query

If a quotation is reported as "not found verbatim", verify whether the turn text exists in PostgreSQL:

```sql
SELECT 
    m.meeting_code,
    s.speaker_label,
    s.role,
    t.turn_index,
    t.start_time_str,
    t.raw_text
FROM transcript_turns t
JOIN meetings m ON t.meeting_id = m.id
LEFT JOIN speakers s ON t.speaker_id = s.id
WHERE m.meeting_code ILIKE 'TS3006%'
  AND t.raw_text ILIKE '%titanium%'
ORDER BY m.meeting_code, t.turn_index;
```

---

## 4. Quotation Normalization Rules

Quotation matching is implemented in `normalize_for_quote_match(text: str)`:

```python
def normalize_for_quote_match(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()
```

### What Normalization Permits:
- **Case variation**: `"Titanium Case"` matches `"titanium case"`.
- **Whitespace variation**: Multiple consecutive spaces, newlines, or tabs collapse to a single space.
- **Leading/trailing whitespace**: Stripped automatically.

### What Normalization Rejects:
- **Paraphrasing**: `"They wanted titanium"` does NOT match `"We initially decided on titanium"`.
- **Punctuation modifications**: Ellipses (`...`) inserted inside quotes fail substring matching unless literally present in raw turn.
- **Cross-turn joins**: Quoting the end of turn 1 and the start of turn 2 together is rejected.

---

## 5. Bounded Retry Monitoring

The agent retries up to `max_validation_retries` (default: 2):

1. **Attempt 0**: Initial `answer_generation`.
2. **Attempt 1**: Re-generation with `validation_feedback` informing the LLM of the specific violation.
3. **Attempt 2**: Final re-generation attempt.
4. **Retry Exhaustion**: If Attempt 2 still fails, the agent discards invalid citations, marks `validation_status = "FAILED"`, and sets a fallback message explaining the failure reasons.

### Health Metrics to Monitor:
- **Validation Pass Rate**: Expected $> 95\%$ on standard benchmark questions.
- **Retry Frequency**: Most questions should pass on Attempt 0; retries should remain $< 15\%$.
- **Exhausted Failures**: Should remain $< 2\%$, indicating robust retrieval and synthesis.
