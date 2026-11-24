# Phase 7: TS3012 Pre-Meeting Briefing

Act as a senior AI engineer.

Implement **Phase 7: TS3012 Pre-Meeting Briefing** in the existing Catalist Meeting Intelligence project.

First inspect the existing Phase 1–6 implementation, especially meeting records, temporal memories, retrieval services, LangGraph workflow, citation validator, and API contracts. Extend the existing architecture without duplicating completed functionality.

## Objective

Generate a pre-meeting briefing for **Team TS3012** using its available meeting history.

The briefing must summarize the team's progress, current decisions, changes in decisions, open actions, owners, and unresolved disagreements. Every factual claim must be supported by verifiable transcript evidence.

## 1. Meeting History and Timeline

Retrieve all available TS3012 meetings and organize them chronologically.

Include:
- Meeting IDs and meeting order.
- Important discussion topics.
- Major decisions.
- Significant changes between meetings.
- Important actions and unresolved issues.

Use actual meeting metadata and transcript records. Report missing or incomplete meeting coverage instead of assuming that all meetings are available.

## 2. Current Decisions

Identify the team's latest supported decisions.

For each decision, include:
- Decision statement.
- Supporting meeting ID.
- Speaker label where available.
- Exact supporting quotation.
- Decision status.
- Earlier decision it replaced, if applicable.

Use temporal memory relationships to distinguish current decisions from historical or superseded decisions.

Do not treat a later statement as a confirmed decision unless the evidence supports that interpretation.

## 3. Decision Changes

Identify decisions that changed over the course of the meetings.

For each change, show:
- Previous decision.
- Updated decision.
- Meeting where the previous decision appeared.
- Meeting where the change occurred.
- Evidence supporting both statements.
- Reason for the change, only when explicitly supported.

Keep the history intact. Never overwrite earlier decisions.

## 4. Open Actions and Owners

Extract outstanding tasks and commitments.

For each action, include:
- Action description.
- Assigned owner, if explicitly supported.
- Source meeting and speaker.
- Current status.
- Exact supporting quotation.

If the owner or status cannot be established, mark it as unknown or uncertain. Do not infer ownership from job roles or conversational context alone.

Exclude completed actions from the open-action list, but retain them in the historical record where relevant.

## 5. Unresolved Disagreements

Identify disagreements that remain unresolved.

For each disagreement, include:
- The issue being disputed.
- Different positions expressed.
- Speakers associated with each position.
- Supporting meeting evidence.
- Whether a later meeting resolved or reopened the issue.

Do not present ordinary discussion or questions as disagreements without evidence.

## 6. Citation and Evidence Validation

Reuse the Phase 6 citation-validation service.

Every factual bullet must have supporting citations containing:
- Meeting ID.
- Speaker label.
- Exact quotation from one original speaker turn.
- Source segment ID.

Enforce:
- At least six words per quotation.
- Exact quotation matching.
- Correct meeting and speaker references.
- No quotations stitched across speaker turns.

Do not generate unsupported claims or citations.

If evidence is unavailable, omit the claim or explicitly identify the information as unknown.

## 7. Briefing Generation

Generate a clear, professional Markdown briefing with this structure:

1. Team and Meeting Coverage
2. Executive Summary
3. Meeting Timeline
4. Current Decisions
5. Changes in Decisions
6. Open Actions and Owners
7. Unresolved Disagreements
8. Items Requiring Attention
9. Evidence and Coverage Limitations

Keep the briefing concise and useful before a team meeting. Prioritize information that participants need to review or act on.

## 8. Backend and API Integration

Implement a briefing service that:

- Generates the TS3012 briefing from persisted meeting and memory data.
- Uses existing retrieval and temporal memory services.
- Validates factual claims and citations before publication.
- Persists generated briefing versions and generation metadata.
- Supports regeneration when new meeting data becomes available.

Expose suitable FastAPI endpoints to:
- Generate a briefing.
- Retrieve the latest briefing.
- Retrieve a previous briefing version.

Follow existing API conventions and Pydantic schemas.

## 9. Testing

Add tests for:

- TS3012 meeting filtering.
- Chronological meeting ordering.
- Current decision identification.
- Decision supersession.
- Open-action extraction.
- Owner identification and unknown owners.
- Disagreement detection and resolution.
- Claim-level citation validation.
- Missing meeting coverage.
- Empty or incomplete team history.
- Briefing persistence and regeneration.

Use mocked LLM responses and controlled transcript fixtures where appropriate.

## 10. Documentation

Update:

- `docs/02_SYSTEM_ARCHITECTURE.md`
- `docs/06_MEMORY_ARCHITECTURE.md`
- `docs/07_TEMPORAL_MEMORY_DESIGN.md`
- `docs/09_AGENT_WORKFLOW.md`
- `docs/11_CITATION_AND_EVIDENCE.md`
- `docs/12_API_DOCUMENTATION.md`
- `docs/15_EVALUATION_FRAMEWORK.md`
- `docs/17_TESTING_STRATEGY.md`
- `docs/20_KNOWN_LIMITATIONS.md`

Add:

- `docs/architecture/TS3012_BRIEFING_PIPELINE.md`
- `docs/operations/BRIEFING_GENERATION_RUNBOOK.md`

Save this prompt in:

`docs/prompts/PHASE_07_TS3012_BRIEFING.md`

Update `docs/prompts/README.md`.

## Acceptance Criteria

- The system retrieves the available TS3012 meeting history.
- Meetings appear in the correct chronological order.
- Current and superseded decisions are distinguishable.
- Decision changes include evidence from both relevant points in time.
- Open actions and owners are evidence-backed.
- Unresolved disagreements are identified without inventing conclusions.
- Every factual briefing bullet has validated citations.
- Missing information and corpus coverage limitations are disclosed.
- The briefing is persisted and can be retrieved.
- Tests pass.
- Existing Phase 1–6 functionality remains operational.
- Documentation reflects the actual implementation.

Do not implement the React frontend or final evaluation/submission package in this phase. These belong to later phases.

At completion, report:
- TS3012 meetings found and processed.
- Briefing sections generated.
- Current decisions and open actions identified.
- Citation-validation results.
- API endpoints.
- Test results.
- Known limitations.

**Stop after Phase 7 and wait for review.**

