# Antigravity Phase Prompts

This directory stores the complete, copy-paste-ready Antigravity implementation prompt for each project phase. Execute one phase at a time. Review its code, documentation, tests, and acceptance checklist before starting the next phase.

## Prompt execution rules

1. Open the repository in Antigravity and paste only the prompt for the current phase.
2. Ask Antigravity to inspect the existing repository and source documents before editing.
3. Require implementation, tests, and documentation—not a plan-only response.
4. Review the final report and verify the acceptance criteria yourself.
5. Do not begin the next phase until the current phase is accepted.
6. Keep the technical documentation under `docs/` synchronized with implementation. This prompt directory is not a replacement for architecture, API, database, security, operations, and evaluation documentation.

## Phase index

| Phase | Prompt | Status | Main outcome |
|---|---|---|---|
| 01 | [PHASE_01_FOUNDATION.md](./PHASE_01_FOUNDATION.md) | Completed | Repository, backend/frontend shell, PostgreSQL, migrations, configuration, observability, docs and tests |
| 02 | [PHASE_02_DATASET_INGESTION.md](./PHASE_02_DATASET_INGESTION.md) | Completed | Safe, idempotent, resumable transcript ingestion and indexing foundation |
| 03 | [PHASE_03_MEMORY_SYSTEM.md](./PHASE_03_MEMORY_SYSTEM.md) | Completed | Persistent short-term and long-term temporal memory, supersession, exact quotation validation |
| 04 | [PHASE_04_HYBRID_RETRIEVAL.md](./PHASE_04_HYBRID_RETRIEVAL.md) | Completed | PostgreSQL FTS + pgvector hybrid retrieval with RRF and evidence packs |
| 05 | [PHASE_05_LANGGRAPH_AGENT.md](./PHASE_05_LANGGRAPH_AGENT.md) | Completed | Stateful multi-step research agent with tool use and checkpoints |
| 06 | [PHASE_06_CITATION_VALIDATION.md](./PHASE_06_CITATION_VALIDATION.md) | In Progress | Deterministic exact-quote and citation validation |
| 07 | `PHASE_07_TS3012_BRIEFING.md` | Planned | Team TS3012 pre-meeting briefing generation |
| 08 | `PHASE_08_REACT_FRONTEND.md` | Planned | Full research, answer review, and briefing UI |
| 09 | `PHASE_09_EVALUATION_SUBMISSION.md` | Planned | Evaluation, failure analysis, scale estimate, `answers.json`, and submission package |

## Documentation outside this folder

The main technical documentation lives directly under `docs/` and its specialist subfolders:

- `docs/architecture/` — architecture and workflow diagrams
- `docs/decisions/` — Architecture Decision Records (ADRs)
- `docs/api/` — API contracts and examples
- `docs/database/` — schema and migration documentation
- `docs/operations/` — setup, runbooks, and troubleshooting
- `docs/evaluation/` — evaluation protocol, ground-truth review, and failure analysis

Each phase prompt must update relevant documents and `docs/10_PHASE_TRACKER.md` as implementation progresses.
