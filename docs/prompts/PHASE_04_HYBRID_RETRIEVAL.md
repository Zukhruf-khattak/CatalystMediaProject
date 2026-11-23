# Phase 4: Hybrid Retrieval System

Act as a senior AI engineer.

Implement **Phase 4: Hybrid Retrieval** in the existing Catalist Meeting Intelligence project.

First inspect the current repository, Phase 1–3 implementations, database schema, ingestion pipeline, temporal memory system, and architecture documentation. Extend the existing implementation without rebuilding completed components.

## Objective

Build a reliable retrieval system that finds relevant evidence across meetings and temporal memories. It must support the project's 25 multi-meeting questions and scale toward 10,000 meetings.

## 1. Hybrid Search

Implement a retrieval pipeline combining:

- **Vector search:** Semantic similarity using the existing embedding model and pgvector.
- **Keyword search:** PostgreSQL full-text search.
- **Temporal memory search:** Retrieve current and historical decisions, actions, disagreements, and related memories.
- **Metadata filtering:** Filter by team, meeting ID, speaker, date/order, memory type, and status.

Use configurable weights for combining retrieval scores. Keep the retrieval strategy modular so weights and methods can be evaluated independently.

## 2. Query Processing

Implement query handling that:

- Accepts natural-language questions.
- Identifies relevant entities, teams, and meeting references where possible.
- Generates search terms for keyword retrieval.
- Uses semantic retrieval for conceptually related evidence.
- Applies metadata filters when available.
- Supports questions requiring evidence from multiple meetings.

Use deterministic code for filtering, ranking calculations, and database operations. Use an LLM only where language understanding genuinely requires it.

## 3. Ranking and Result Fusion

Implement a ranking strategy such as Reciprocal Rank Fusion (RRF) to combine keyword and vector results.

The retrieval response must include:

- Original query.
- Retrieved transcript segments.
- Related temporal memories.
- Meeting IDs and speaker labels.
- Exact transcript quotations.
- Source segment references.
- Retrieval method and ranking scores.

Preserve source traceability throughout the pipeline.

## 4. Temporal Retrieval

Integrate Phase 3 memory relationships.

When retrieving decisions:

- Prioritize supported current decisions.
- Retain historical and superseded decisions when relevant.
- Include supporting evidence for changes.
- Surface unresolved disagreements separately.
- Never treat the latest statement as automatically authoritative without supporting evidence.

## 5. Evaluation

Create a retrieval evaluation dataset using the provided `questions.json` and available transcript evidence.

Evaluate:

- Recall@5 and Recall@10.
- Precision@5 and Precision@10.
- Mean Reciprocal Rank (MRR).
- Retrieval latency.
- Performance of keyword-only, vector-only, and hybrid retrieval.

Manually inspect representative queries and document retrieval failures.

Do not invent relevance labels. Clearly distinguish manually verified labels from unverified results.

## 6. Testing

Add tests for:

- Keyword retrieval.
- Vector retrieval.
- Hybrid result fusion.
- Metadata filtering.
- Multi-meeting retrieval.
- Temporal memory retrieval.
- Duplicate result handling.
- Empty and malformed queries.
- Team isolation.
- Ranking consistency.

Use mocked embeddings or controlled test data where appropriate.

## 7. Documentation

Update the existing documentation under `docs/`:

- `02_SYSTEM_ARCHITECTURE.md`
- `03_DATA_AND_MEMORY_DESIGN.md`
- `04_RETRIEVAL_AND_AGENT_DESIGN.md`
- `06_API_CONTRACT.md`
- `07_TESTING_AND_EVALUATION_PLAN.md`
- `09_DEPLOYMENT_AND_OPERATIONS.md`
- `10_PHASE_TRACKER.md`

Add:

- `docs/architecture/HYBRID_RETRIEVAL_PIPELINE.md`
- `docs/evaluation/RETRIEVAL_EVALUATION.md`
- `docs/operations/RETRIEVAL_RUNBOOK.md`

Save this prompt in:

`docs/prompts/PHASE_04_HYBRID_RETRIEVAL.md`

Update `docs/prompts/README.md`.

## Acceptance Criteria

- Keyword and vector retrieval work independently.
- Hybrid retrieval combines both result sets.
- Temporal memories are included in retrieval.
- Results retain exact source evidence and meeting references.
- Multi-meeting questions can retrieve evidence from multiple meetings.
- Retrieval metrics are calculated and documented.
- Tests pass.
- Existing Phase 1–3 functionality remains operational.
- Documentation reflects the implemented system.

At completion, report changed files, API endpoints, retrieval metrics, test results, commands to run, and known limitations.

Do not implement the LangGraph QA agent, citation validation, TS3012 briefing, or React frontend in this phase. These belong to later phases.

**Stop after Phase 4 and wait for review.**

