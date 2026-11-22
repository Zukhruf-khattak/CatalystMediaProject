# 05 — Citation and Evidence Policy

## 1. Absolute Authority: The Catalist Assessment Brief
The assessment explicitly defines citation rules:
> *"Back every answer with one to three citations. A citation is a meeting id and a quote of at least six words copied exactly from that transcript, from within one speaker turn. Quotes are checked automatically (case and spacing are ignored); paraphrases fail."*

---

## 2. Deterministic Validation Rules

Every candidate citation must pass four deterministic checks:

1. **Existence in Stored Turn**:
   - The quote must exist as a contiguous or normalized substring in the transcript of the specified `meeting_id`.
2. **Single Turn Boundary Rule**:
   - The quote cannot cross speaker turn boundaries. Splicing two turns together is an automatic failure.
3. **Minimum Length Rule**:
   - The quote must contain at least **6 whitespace-delimited words**:
     $$\text{word\_count} = \text{len}(\text{re.findall}(r'\b\w+\b', \text{quote})) \ge 6$$
4. **Case and Whitespace Invariance**:
   - Comparison normalizes multiple whitespace characters (`\s+` -> ` `) and performs case-insensitive matching (`quote.lower() in turn_text.lower()`).

---

## 3. Tool-Fit Boundary: Model vs. Deterministic Code
- **Model Responsibility**: Identifying pertinent evidence, drafting answers, selecting candidate excerpts from retrieved speaker turns.
- **Code Responsibility**:
  - Exact string matching against the database.
  - Rejecting candidate quotes that fail the length or single-turn constraints.
  - Automatically snapping candidate quotes to exact database substrings when punctuation or casing slightly differs.

---

## 4. Phase Boundaries
- **Implemented in Phase 1**: Citation policy, contract definitions, and ADR-005.
- **Deferred to Phase 6**: Production citation validation engine and test suite.
