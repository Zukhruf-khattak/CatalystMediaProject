# Antigravity Prompt — Phase 3: Temporal Meeting Memory

**Project:** Catalist Meeting Intelligence Agent  
**Phase:** 03 of 09  
**Mode:** Inspect first, extend architecture, implement, test, document  
**Primary outcome:** A persistent, chronologically aware memory system that extracts atomic decisions, actions, preferences, and disagreements from ingested transcripts, validates quotations against ground truth, and tracks temporal supersession across meetings.

---

Act as a senior AI/backend engineer.

Implement Phase 3: Temporal Meeting Memory in the existing
Catalist Meeting Intelligence project.

First inspect the existing repository, Phase 1 and Phase 2
implementation, database schema, ingestion pipeline and ADRs.
Extend the existing architecture instead of rebuilding it.

OBJECTIVE:
Create persistent memory that understands how information
changes across meetings.

1. MEMORY EXTRACTION

Extract atomic records for:
- Decisions and changes to previous decisions.
- Actions, commitments and their owners.
- Product/team preferences and requirements.
- Disagreements and unresolved issues.
- Relevant entities and references.

Use the existing LLM provider abstraction. Prefer a free/local
model. Do not require a paid API key.

2. MEMORY STORAGE

Store each memory with:
- Unique ID and memory type.
- Statement and team ID.
- Source meeting and transcript segment references.
- Exact supporting transcript quotation.
- Speaker label and meeting order.
- Status: current, superseded, open, resolved or rejected.
- Confidence and extraction version.
- Links to related memories.

Never overwrite historical memories.

3. TEMPORAL REASONING

Connect related memories using relationships such as:
- supports
- contradicts
- updates
- supersedes
- resolves
- reopens

Example:
Meeting A: The team decides to use Design A.
Meeting C: The team changes its decision to Design B.

The system must preserve both decisions and identify Design B
as the current decision only when the evidence supports it.

Keep ambiguous relationships unresolved.

4. EVIDENCE VALIDATION

Every memory must reference its original transcript evidence.

Implement exact quotation validation against stored transcript
segments. Reject fabricated or modified quotations.

Do not infer speaker identity or action ownership without evidence.

5. RETRIEVAL

Implement a paginated memory retrieval service supporting:
- Team filtering.
- Meeting/order filtering.
- Memory type and status filtering.
- Text/vector similarity where available.

Every result must include its source evidence.

6. TESTING

Test:
- Memory extraction and schema validation.
- Exact quotation verification.
- Duplicate prevention.
- Decision supersession.
- Unresolved disagreements.
- Action ownership.
- Partial failures and retries.
- Team isolation.

Use mocked LLM responses for unit tests.

7. DOCUMENTATION

Update the main docs/ folder:
- 03_DATA_AND_MEMORY_DESIGN.md
- 04_RETRIEVAL_AND_AGENT_DESIGN.md
- 07_TESTING_AND_EVALUATION_PLAN.md
- 08_SECURITY_AND_PRIVACY.md
- 09_DEPLOYMENT_AND_OPERATIONS.md
- 10_PHASE_TRACKER.md

Add:
- architecture/TEMPORAL_MEMORY_PIPELINE.md
- database/MEMORY_SCHEMA.md
- operations/MEMORY_EXTRACTION_RUNBOOK.md

Save this prompt in:
docs/prompts/PHASE_03_MEMORY_SYSTEM.md

Update docs/prompts/README.md.

8. ACCEPTANCE CRITERIA

- Memories persist in PostgreSQL.
- Every memory has verifiable source evidence.
- Exact quotation validation works.
- Historical decisions are preserved.
- Supported temporal changes are represented correctly.
- Ambiguous changes are not automatically accepted.
- Extraction is resumable and idempotent.
- Tests pass.
- Documentation is updated.

At completion, report changed files, migrations, memory counts,
test results, commands and known limitations.

Do not implement the LangGraph QA agent or TS3012 briefing.
Those belong to later phases.

Stop after Phase 3 and wait for review.

