# 00 — Project Overview: Catalist Meeting Intelligence Agent

## Executive Summary
The **Catalist Meeting Intelligence Agent** is an autonomous agentic intelligence system designed to convert hundreds of hours of raw meeting transcripts into a structured, temporally aware conversational memory store and automated team briefing engine.

The system is evaluated against the **AMI Meeting Corpus** (138 real-world meeting transcripts, ~676,000 words across 35 design teams designing a consumer TV remote control) and architecturally built to scale to an enterprise corpus of **10,000+ meetings**.

---

## 1. Problem Statement
In fast-moving organizations, founders and teams record hundreds of meetings. Over time:
- Key decisions shift across meetings without explicit cross-references.
- Commitments and promises made by specific individuals are lost or untracked.
- Disagreements and tradeoffs are forgotten when new members join or final deadlines approach.
- Prior to high-stakes milestone meetings, nobody reads hundreds of pages of past transcripts to synthesize current status, open actions, or unresolved debates.

Naive RAG approaches that dump raw transcripts into a single massive context window fail because:
1. They collapse temporal order (a decision in meeting *c* overturning meeting *a* looks identical without sequence awareness).
2. They do not scale linearly to thousands of hours of speech.
3. They hallucinate quotes and misattribute statements across multi-speaker turns.

---

## 2. Target Users & Personas
- **The Founder / Executive**: Needs reliable, cited answers to cross-meeting strategic questions without wading through transcripts.
- **Project Teams (e.g. Team TS3012)**: Need automated, synthesized pre-meeting briefs before pivotal design milestones.
- **Auditors / Evaluators**: Require word-for-word verified citations with exact speaker and meeting provenance.

---

## 3. Assessment Deliverables (Catalist Media)
As specified in the Catalist build-test brief:
1. **Runnable Codebase**: Clean, maintainable, locally executable repository.
2. **`answers.json`**:
   - 25 cross-meeting question answers with 1–3 exact citations per answer (meeting ID + verbatim quote of >= 6 words within a single speaker turn).
   - Team TS3012 pre-meeting brief synthesized with exact citations.
3. **10 Independently Authored & Verified Evaluation Questions**: Self-authored questions with manual ground-truth citations from the transcripts to benchmark retrieval accuracy.
4. **Three Documented Failures**: Honest analysis of failure modes and edge cases encountered by the agent.
5. **Scale & Cost Estimate**: Concrete computational, token, and time estimates for processing 1,000 meetings.
6. **Technical Write-up (~1 Page)**: Architecture, model-vs-code boundaries, failure points, and enterprise scale roadmap.
7. **Walkthrough / Demo**: 3–5 minute recorded or live demonstration.

---

## 4. Current Phase Boundaries

### Implemented in Phase 1 (Current)
- Repository architecture: modular backend (`FastAPI`), component-driven frontend (`React + Vite + Tailwind`).
- Infrastructure: Docker Compose with PostgreSQL 16 + pgvector, named volume persistence, health checks.
- Baseline database migration via Alembic (pgvector extension initialization).
- Typed settings via `pydantic-settings` and safe `.env.example`.
- Reliability: Structured logging, UUID request-ID middleware, centralized exception handling.
- Observability: Optional, non-breaking LangSmith integration hooks.
- System health and readiness endpoints (`/api/v1/health`, `/api/v1/ready`).
- Complete documentation suite and architectural diagrams.

### Designed for Later Phases (Deferred)
- **Phase 2**: Safe transcript parsing, speaker-turn ingestion, local embeddings (`all-MiniLM-L6-v2`), lexical + semantic index creation.
- **Phase 3**: Persistent short-term and long-term temporal memory schemas and extraction.
- **Phase 4**: Hybrid retrieval service combining PostgreSQL FTS and pgvector via Reciprocal Rank Fusion (RRF).
- **Phase 5**: LangGraph multi-step research agent with state machine, loop bounds, and tool use.
- **Phase 6**: Deterministic citation validator enforcing exact string match, single turn constraint, and minimum length.
- **Phase 7**: Team TS3012 pre-meeting brief generation pipeline.
- **Phase 8**: Interactive React frontend for querying, reviewing answers, and viewing briefs.
- **Phase 9**: Rigorous benchmark evaluation, failure analysis, scale estimation, and final submission packaging.

### Explicitly Not in Scope
- Live audio processing / speech-to-text (the project ingests text transcripts).
- Proprietary closed-source vector database SaaS (Chroma/Pinecone cloud).
- GPU/CUDA acceleration requirement for base developer workstation.

