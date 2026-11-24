# Phase 6: Citation and Evidence Validation

Act as a senior AI engineer.

Implement **Phase 6: Citation and Evidence Validation** in the existing Catalist Meeting Intelligence project.

First inspect the completed Phase 1–5 implementation, especially transcript storage, speaker turns, retrieval results, LangGraph workflow, API schemas, and database models. Extend the existing architecture.

## Objective

Build a deterministic citation-validation layer that ensures every generated answer is supported by real transcript evidence.

## 1. Citation Structure

Each citation must contain:

- Meeting ID.
- Team ID.
- Speaker label.
- Exact quotation copied from one original speaker turn.
- Source segment/turn ID.

Each answer must follow the Catalist requirements:

- One to three plain sentences.
- One to three citations.
- Evidence from at least two meetings of the named team.
- Each quotation must contain at least six words.
- Preserve speaker letters; include speaker roles only when supported by the transcript.

## 2. Exact Quote Validation

Implement a deterministic validation service.

For every citation:

1. Confirm that the meeting exists.
2. Confirm that the meeting belongs to the expected team.
3. Confirm that the referenced speaker turn exists.
4. Verify that the quotation matches the original speaker turn.
5. Enforce the six-word minimum.
6. Reject quotations stitched together from multiple turns.
7. Verify that the citation references the correct source segment.

Follow the supplied checker’s matching behavior: case and spacing may be normalized, but wording and punctuation must otherwise remain faithful.

Never use an LLM to decide whether a quotation is exact.

## 3. Answer-Level Validation

Validate the complete answer against these rules:

- Answer contains one to three sentences.
- Citation count is between one and three.
- At least two distinct meetings from the named team contribute evidence.
- Every citation passes individual validation.
- Citations support the claims they are attached to.
- No unsupported factual claims are introduced.

Return structured validation results with individual failure reasons.

## 4. LangGraph Integration

Integrate validation into the Phase 5 agent workflow.

Add a citation-validation node after answer generation.

If validation fails:

- Send structured errors back to the answer-generation node.
- Allow a configurable limited retry.
- Regenerate only when useful evidence is available.
- Return an explicit validation failure or insufficient-evidence response when retries are exhausted.

Never silently remove invalid citations or fabricate replacements.

## 5. Structured Output

Use Pydantic schemas for answers, citations, and validation results.

Provide a consistent response containing:

- Answer text.
- Citation objects.
- Validation status.
- Validation errors, if any.
- Supporting meeting IDs.

Keep the response compatible with the existing API and future React frontend.

## 6. Testing

Add tests covering:

- Exact quotation matches.
- Case and spacing normalization.
- Modified or fabricated quotations.
- Quotes shorter than six words.
- Quotes stitched across turns.
- Incorrect meeting IDs.
- Incorrect team IDs.
- Incorrect speaker labels.
- Duplicate meeting citations.
- Evidence from only one meeting.
- Unsupported answer claims.
- Successful validation and retry behavior.
- Insufficient evidence after retries.

Use controlled transcript fixtures and mocked LLM responses.

## 7. Documentation

Update:

- `docs/02_SYSTEM_ARCHITECTURE.md`
- `docs/04_RETRIEVAL_AND_RAG.md`
- `docs/09_AGENT_WORKFLOW.md`
- `docs/11_CITATION_AND_EVIDENCE.md`
- `docs/12_API_DOCUMENTATION.md`
- `docs/15_EVALUATION_FRAMEWORK.md`
- `docs/17_TESTING_STRATEGY.md`
- `docs/20_KNOWN_LIMITATIONS.md`

Add:

- `docs/architecture/CITATION_VALIDATION_PIPELINE.md`
- `docs/operations/CITATION_VALIDATION_RUNBOOK.md`

Save this prompt in:

`docs/prompts/PHASE_06_CITATION_VALIDATION.md`

Update `docs/prompts/README.md`.

## Acceptance Criteria

- Every citation is checked against an original speaker turn.
- The six-word minimum is enforced.
- Cross-meeting evidence requirements are enforced.
- Incorrect meeting, team, or speaker references are rejected.
- Invalid citations cannot reach the final successful answer.
- LangGraph retries validation failures within a configured limit.
- Insufficient evidence produces an explicit response.
- Tests pass.
- Existing Phase 1–5 functionality remains operational.
- Documentation reflects the implementation.

Do not implement the TS3012 briefing or React frontend in this phase. These belong to later phases.

At completion, report changed files, validation rules, API changes, test results, example valid and invalid citations, and known limitations.

**Stop after Phase 6 and wait for review.**

