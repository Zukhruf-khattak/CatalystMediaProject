# 01 — Requirements Specification

## 1. Overview and Traceability Matrix
This document establishes the functional and non-functional requirements for the Catalist Meeting Intelligence Agent, mapped directly to the original Catalist build-test brief (`Catalist_Agentic_AI_Intern_Build_Test.pdf`) and the Phase technical specifications.

---

## 2. Functional Requirements (FR)

| Req ID | Requirement Description | Brief Reference | Phase Target | Status |
|---|---|---|---|---|
| **FR-01** | **Ingest AMI Transcripts**: Ingest 138 transcripts (~676,000 words) into queryable store. | Brief p.1 §1 | Phase 2 | Planned |
| **FR-02** | **Speaker Turn Granularity**: Preserve speaker label (A–D), role if known, timestamp, and order. | Brief p.1 §1; questions.json | Phase 2 | Planned |
| **FR-03** | **Temporal Sequence Tracking**: Track meeting order (a -> b -> c -> d) and recognize superseding decisions. | Brief p.1 §38 | Phase 3 | Planned |
| **FR-04** | **Cross-Meeting Retrieval**: Retrieve evidence across multiple meetings of the same or different teams. | questions.json §2 | Phase 4 | Planned |
| **FR-05** | **Answer 25 Questions**: Synthesize answers in 1–3 plain sentences per question. | questions.json §3 | Phase 5 | Planned |
| **FR-06** | **Deterministic Citations**: Back every answer with 1–3 citations (meeting ID + >= 6 words exact quote in single turn). | questions.json §5 | Phase 6 | Planned |
| **FR-07** | **Team TS3012 Pre-Meeting Brief**: Summarize decisions, changes, open actions + owners, and disagreements. | Brief p.1 §25 | Phase 7 | Planned |
| **FR-08** | **Author-Verified Benchmark**: Include at least 10 independently authored & manually verified test questions. | Brief p.2 §45 | Phase 9 | Planned |
| **FR-09** | **Documented Failures**: Analyze and document at least 3 genuine agent failure modes. | Brief p.2 §48 | Phase 9 | Planned |
| **FR-10** | **System Health & Readiness**: Expose `/api/v1/health` and `/api/v1/ready` for operational monitoring. | Phase 1 Spec §5.1 | Phase 1 | **Implemented** |
| **FR-11** | **Interactive Web Interface**: Visual dashboard showing status, question queries, and briefs. | Phase 1 Spec §6 | Phase 1/8 | **Phase 1 Shell Implemented** |

---

## 3. Non-Functional Requirements (NFR)

### 3.1 Architectural Scale & Performance
- **NFR-01 (10,000 Meeting Scale Design)**: All storage schemas, indexes, and retrieval algorithms must be designed to accommodate 10,000 meetings (approx. 50,000,000 words / 2,500,000 speaker turns) without requiring in-memory context stuffing.
- **NFR-02 (Bounded Context Window)**: Search queries must retrieve bounded evidence packs (top-k speaker turns, maximum 4,000 tokens per reasoning cycle).
- **NFR-03 (Response Latency)**: Health and readiness endpoints must respond within 100ms under standard local load.

### 3.2 Reliability and Determinism
- **NFR-04 (Quote Verification Guarantee)**: 100% of generated citations must be verified against database records with zero tolerance for paraphrasing or cross-turn splices.
- **NFR-05 (Resilient Tracing)**: Application must start and operate smoothly even if LangSmith or external telemetry is unreachable or unconfigured.

### 3.3 Security, Privacy, and Environment Constraints
- **NFR-06 (No Mandatory Paid Keys)**: The entire foundation, ingestion, testing, and evaluation pipeline must be executable using local-first tools (Ollama/CPU embeddings) or optional free-tier keys.
- **NFR-07 (Secret Safety)**: Credentials, API tokens, and connection strings must be read strictly from environment variables and excluded from version control.
- **NFR-08 (Resource Footprint)**: Foundation services must run on consumer machines with <= 16GB RAM and no discrete GPU.

