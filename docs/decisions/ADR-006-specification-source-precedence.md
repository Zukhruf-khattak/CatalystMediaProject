# ADR-006: Specification Source Precedence and Conflict Resolution

## Status
Accepted

## Context
The project operates under two primary governing documents:
1. **The Original Catalist Build-Test Brief** (`Catalist_Agentic_AI_Intern_Build_Test.pdf` and `questions.json`): Authored by Catalist Media, defining assessment criteria, grading rules, data characteristics, evaluation tasks (25 questions, Team TS3012 brief), and submission deliverables.
2. **Phase Prompt Specifications** (`PHASE_01_FOUNDATION.md`, `PHASE_02_DATASET_INGESTION.md`, etc.): Detailed engineering guidelines defining architectural tiers, technology baselines, modular boundaries, acceptance criteria, and phase sequencing.

A formal rule of precedence is required whenever potential ambiguities or conflicts arise between assessment rules and implementation patterns.

## Decision
1. **Assessment Authority**: The original Catalist brief (`Catalist_Agentic_AI_Intern_Build_Test.pdf`) and `questions.json` are the supreme authority on:
   - What the agent must do (answering 25 questions, citing exact quotes of >= 6 words within one speaker turn, generating the TS3012 brief).
   - Evaluation methodology (10 author-verified questions, 3 documented failures, 1,000 meeting cost/scale estimation).
   - Final deliverables (`answers.json`, 1-page writeup, demo walkthrough).
2. **Implementation Baseline**: The Phase Technical Specifications govern:
   - Technology baseline (Python 3.12, FastAPI, PostgreSQL 16 + pgvector, Alembic, React + TypeScript + Vite, Tailwind CSS).
   - Layered architecture and package structures.
   - Engineering discipline (automated tests, type safety, observability, Docker Compose).
3. **Precedence Hierarchy**:
   - In matters of scoring, citation validity, data handling, and deliverable format: **Catalist Brief > Technical Spec**.
   - In matters of engineering architecture, framework selection, and code structure: **Technical Spec > Ad-hoc patterns**.
   - If a technical spec rule would cause an assessment failure (e.g. proposing paraphrased citations), the Catalist Brief rule overrides it immediately.

## Consequences
- Transparent alignment with evaluator expectations.
- Zero ambiguity during implementation.

