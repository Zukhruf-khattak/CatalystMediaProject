# Changelog

All notable changes to the **Catalist Meeting Intelligence Agent** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - Phase 09 Release - 2026-11-24

### Added
- **Full Corpus Ingestion Deliverable**: Complete ingestion of all 138 AMI meeting transcripts (48,148 turns, 676,745 words) with local dense vectors (`all-MiniLM-L6-v2`) in `catalist.db`.
- **25 Benchmark Assessment Answers (`artifacts/answers.json`)**: Grounded answers for questions Q01 through Q25, achieving 100% pass rate under deterministic validation (1–2 plain sentences, 1–3 citations, verbatim $\ge 6$-word single-turn quotations, spanning $\ge 2$ meetings per team).
- **Executive TS3012 Briefing (`artifacts/briefing.md`)**: Full 9-section pre-meeting intelligence briefing preceding meeting TS3012d with 7 verified citations.
- **Custom Capability Benchmark Report (`artifacts/evaluation_report.md`)**: 10 cross-meeting challenge questions across 8 capabilities, 3 deep failure case studies, empirical latency profiles, and enterprise 1,000 / 10,000-meeting scaling analysis.
- **High-Density Technical Report (`technical_report.md`)**: Executive architecture, temporal memory graph, hybrid retrieval, agent boundaries, and empirical evaluation report.
- **Live Demo Walkthrough Script (`docs/DEMO_SCRIPT.md`)**: Step-by-step 3–5 minute demonstration guide for evaluating the system.

---

## [0.8.0] - Phase 08: React Frontend - 2026-11-24

### Added
- Complete React 18 + TypeScript + Vite 5 frontend interface with Tailwind CSS, shadcn/ui, Lucide icons, and TanStack Query.
- Responsive layout with Sidebar, Topbar, and 6 core feature views:
  - Research Assistant (`/research`) with streaming answers and validation status pills.
  - Citation Context Viewer (`/citations`) with turn inspector and ±2 turn surrounding context modal.
  - Temporal Memory Explorer (`/memory`) with relationship graph badges.
  - Decision Timeline (`/decisions`) with meeting evolution sequence.
  - Pre-Meeting Briefing (`/briefing`) with 9-section markdown renderer and version history.
  - Ingestion Monitor (`/ingestion`) with corpus statistics and job history.
- Server-Sent Events (SSE) streaming integration for live LangGraph execution state visualization.

---

## [0.7.0] - Phase 07: TS3012 Pre-Meeting Briefing - 2026-11-24

### Added
- `BriefingService` generating comprehensive pre-meeting briefings for target meetings (TS3012d).
- 9-section structured format: Team/Meeting Coverage, Executive Summary, Meeting Timeline, Current Decisions, Decision Changes, Open Actions, Unresolved Disagreements, Items Requiring Attention, Evidence Limitations.
- Briefing database persistence and caching model (`Briefing`).
- REST endpoints (`/api/v1/briefings/*`) and CLI command `catalist brief --team TS3012`.

---

## [0.6.0] - Phase 06: Citation and Evidence Validation - 2026-11-24

### Added
- Deterministic `CitationValidationService` enforcing exact verbatim substring matching, single-turn boundary constraints, $\ge 6$-word minimum, and multi-meeting requirements ($\ge 2$ meetings).
- Speaker letter and role verification against stored metadata.
- Lexical claim overlap guardrail ($\ge 20\%$ substantive token overlap).
- Bounded retry loops and fallback generation in LangGraph agent state graph.

---

## [0.5.0] - Phase 05: LangGraph Multi-Step Research Agent - 2026-11-23

### Added
- Stateful 8-node LangGraph research agent (`input_validation` -> `query_analysis` -> `retrieval_planning` -> `tool_execution` -> `evidence_assessment` -> `answer_generation` -> `response_validation` -> `final_response`).
- 5 retrieval tools: `hybrid_search`, `search_temporal_memory`, `get_meeting_details`, `get_related_meetings`, `get_memory_history`.
- Session persistence (`AgentSession`) and CLI command `catalist ask`.

---

## [0.4.0] - Phase 04: Hybrid Retrieval System - 2026-11-23

### Added
- Hybrid retrieval engine combining dense vector search (`pgvector`) and lexical search (`FTS5` / PostgreSQL `tsvector`).
- Reciprocal Rank Fusion (`RRF`) scoring with configurable weights ($k=60$).
- Structured evidence packs (`EvidencePackResponse`) and CLI command `catalist retrieve`.

---

## [0.3.0] - Phase 03: Temporal Meeting Memory - 2026-11-23

### Added
- Relational schema for `Memory`, `MemoryRelationship`, and `MemoryExtractionRun`.
- Append-only temporal graph with typed relationships (`updates`, `contradicts`, `supports`).
- Lifecycle status tracking (`CURRENT`, `SUPERSEDED`, `OPEN`, `RESOLVED`, `REJECTED`).
- Local-first LLM extraction interface (`OllamaLLMClient`).

---

## [0.2.0] - Phase 02: Dataset Ingestion & Indexing - 2026-11-23

### Added
- Safe zip extractor with Zip Slip defense.
- Deterministic parser for AMI meeting transcript headers, speaker rosters, and turn boundaries.
- Relational persistence in PostgreSQL/SQLite for teams, meetings, speakers, and turns.
- Dense embeddings via `sentence-transformers/all-MiniLM-L6-v2`.

---

## [0.1.0] - Phase 01: Repository Foundation & Architecture Baseline - 2026-11-22

### Added
- Initial modular monolith architecture (FastAPI backend + React frontend).
- Docker Compose configuration for PostgreSQL 16 + `pgvector`.
- Baseline Alembic database migrations and typed Pydantic configuration.
- Architectural Decision Records (ADR-001 through ADR-006).

