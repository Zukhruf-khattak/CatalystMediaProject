# Phase 1 — Repository Foundation, Architecture Baseline, and Engineering Setup

**Project:** Catalist Meeting Intelligence Agent  
**Execution environment:** Antigravity IDE  
**Phase status:** Ready to execute  
**Depends on:** Original Catalist build-test brief, supplied dataset archive, and `Catalist_Phase_1_Technical_Specification.md`  
**Next phase:** Phase 2 — Dataset ingestion

---

## Copy-paste prompt for Antigravity

You are the senior software architect and implementation engineer responsible for establishing the foundation of the **Catalist Meeting Intelligence Agent**. Work directly in the currently opened repository. Implement this phase, run the checks, and document the actual result. Do not merely provide a plan or generate placeholder files.

## 1. First inspect the source material and repository

Before changing files:

1. Inspect the complete existing repository, including hidden configuration files, current Git status, and existing documentation.
2. Read the original Catalist build-test brief supplied with the project.
3. Read `Catalist_Phase_1_Technical_Specification.md` if it is present in the repository or project workspace. If it is not present, locate the supplied technical specification. Do not silently recreate it from memory.
4. Inspect the supplied dataset archive's top-level structure and `questions.json` without implementing ingestion in this phase. Confirm the actual filenames and format.
5. Treat the original Catalist brief as the assessment authority and the technical specification as the implementation baseline. If they conflict, record the conflict in `docs/decisions/` and explain which source takes precedence.
6. Preserve existing working code and user changes. Do not overwrite or delete files just to match a proposed folder tree.

The assessment requires a system that can ingest 138 AMI meeting transcripts (about 676,000 words), answer 25 cross-meeting questions with exact transcript quotations, and generate a cited pre-meeting brief for Team TS3012. The system must be designed for a future 10,000-meeting corpus. It must demonstrate temporal memory, multi-step retrieval/reasoning, deterministic citation checking, at least 10 independently authored and manually verified evaluation questions, three documented failures, and an estimate for processing 1,000 meetings. The final submission includes runnable code, README, `answers.json`, an approximately one-page technical write-up, and a 3–5 minute walkthrough/demo.

## 2. Objective of this phase

Establish a clean, runnable, documented, testable foundation for the project. At the end of Phase 1:

- The repository has a maintainable backend/frontend/docs structure.
- The backend starts and exposes health and readiness endpoints.
- The frontend starts and displays a professional project shell with backend connectivity status.
- PostgreSQL starts locally through Docker Compose and the backend can connect to it.
- Alembic is configured and can apply the initial baseline migration.
- Configuration is typed, validated, and loaded from environment variables.
- Logging, error handling, request IDs, and basic observability hooks are established.
- LangSmith integration is configurable and safely disabled when credentials are absent.
- The architecture, decisions, setup, environment variables, and phase plan are documented.
- Automated backend and frontend foundation tests pass.

Do not implement transcript parsing, bulk ingestion, embeddings, memory extraction, hybrid retrieval, LangGraph research, citation validation, or TS3012 briefing in this phase. Those belong to later phases.

## 3. Locked technology baseline

Use these technologies unless the existing repository has a documented, working decision that must be preserved:

### Backend
- Python 3.12
- FastAPI
- Pydantic v2 and pydantic-settings
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16
- psycopg (v3) or the SQLAlchemy-compatible PostgreSQL driver selected consistently
- Pytest and HTTPX for tests
- Ruff for linting/formatting
- Structured application logging with Python standard logging or a lightweight structured logger

### Frontend
- React + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui-compatible component setup (install only the required dependencies)
- Lucide React icons
- React Router
- TanStack Query
- Vitest + React Testing Library

### Infrastructure and observability
- Docker and Docker Compose
- PostgreSQL 16 with pgvector extension available/enabled for later phases
- LangSmith Developer integration through environment configuration; no credentials are required to run locally
- Mermaid diagrams in Markdown
- Git and `.gitignore`

### Model and API key policy
The project must remain usable without paid API keys. Do not make a paid provider mandatory in Phase 1. Configure provider settings through environment variables only. Hosted Gemini can be an optional provider if available on the user's free account; Ollama is the local fallback. Local embeddings will be added in a later phase. Do not download large models during foundation setup.

The developer machine may have limited RAM. Keep the default foundation lightweight and CPU-compatible. Do not require CUDA or a GPU.

## 4. Repository structure

Create or align the repository to this structure, preserving existing files and adapting names only when necessary:

```text
catalist-meeting-intelligence/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/
│   │   └── types/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── artifacts/
│   ├── evaluations/
│   └── submissions/
├── docs/
│   ├── prompts/
│   ├── architecture/
│   ├── decisions/
│   ├── api/
│   ├── database/
│   ├── operations/
│   ├── evaluation/
│   ├── 00_PROJECT_OVERVIEW.md
│   ├── 01_REQUIREMENTS_SPECIFICATION.md
│   ├── 02_SYSTEM_ARCHITECTURE.md
│   ├── 03_DATA_AND_MEMORY_DESIGN.md
│   ├── 04_RETRIEVAL_AND_AGENT_DESIGN.md
│   ├── 05_CITATION_AND_EVIDENCE_POLICY.md
│   ├── 06_API_CONTRACT.md
│   ├── 07_TESTING_AND_EVALUATION_PLAN.md
│   ├── 08_SECURITY_AND_PRIVACY.md
│   ├── 09_DEPLOYMENT_AND_OPERATIONS.md
│   └── 10_PHASE_TRACKER.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile or equivalent task runner
└── README.md
```

The `docs/prompts/` directory is only one part of documentation. Maintain the other technical documentation listed above throughout the project. Add diagrams under `docs/architecture/` and ADRs under `docs/decisions/`. Do not put all documentation into the prompts folder.

## 5. Backend foundation implementation

Implement the following:

### 5.1 Application structure
- Use a modular, layered FastAPI structure.
- Keep route handlers thin; business logic belongs in services.
- Keep configuration, database setup, logging, and exception handling in `core/` or `db/` modules.
- Add `/api/v1/health` for liveness and `/api/v1/ready` for dependency readiness.
- Health must not expose secrets, internal stack traces, or database credentials.
- Add a root route or OpenAPI metadata with project name and version.
- Configure CORS from an explicit environment variable list; do not use unrestricted wildcard CORS in production configuration.

### 5.2 Configuration
Create a typed settings module using Pydantic Settings. Include at minimum:
- app name, environment, debug flag, API prefix
- backend host/port
- frontend allowed origins
- PostgreSQL URL and pool settings
- LangSmith tracing enabled flag, project name, endpoint if needed, and API key
- LLM provider/model settings and optional Gemini/Ollama credentials/base URL
- log level

Provide `.env.example` with safe placeholders only. Never commit a real `.env`, API key, password, or token. Validate required settings at startup and provide actionable error messages.

### 5.3 Database setup
- Add SQLAlchemy 2 engine/session configuration with clean dependency injection.
- Add Alembic and configure it to read the database URL from application settings.
- Enable/check pgvector extension in a reversible initial migration or a dedicated extension migration, depending on the selected migration strategy.
- Create only the minimal foundation metadata needed now (for example, no speculative domain tables unless the technical spec explicitly requires them in Phase 1).
- Verify migration upgrade and downgrade behavior where practical.
- Add a database readiness check with a short timeout.

### 5.4 Reliability and observability foundation
- Add structured logs with timestamp, severity, logger, request ID, and message.
- Add request ID middleware; accept a valid incoming request ID or generate one, and return it in response headers.
- Add centralized exception handling with safe client-facing errors.
- Add LangSmith tracing configuration through supported LangChain/LangSmith environment variables or the current SDK integration. Do not invent SDK methods. Confirm installed package API from its actual version/docs before use.
- If tracing is disabled or credentials are missing, the app must continue normally and log that tracing is disabled without failing startup.
- Do not send complete transcripts or secrets to traces. Establish a redaction/metadata-only policy now; later phases can add carefully selected input/output tracing.
- Add basic startup/shutdown lifecycle handling.

## 6. Frontend foundation implementation

Build a polished but restrained project shell, not a generic template dashboard.

### Required screens/components
- Responsive application layout with sidebar or top navigation.
- Product name: **Catalist Meeting Intelligence**.
- Overview page with a concise explanation of the product workflow: ingest meetings → build memory → research questions → validate evidence → generate team brief.
- System status panel showing backend API and database readiness based on actual API responses.
- Clear loading, success, degraded, and error states.
- A small project status area showing phase progress as static configuration for now; do not fake operational metrics.
- A responsive layout that works on desktop and narrower screens.

### UI quality requirements
- Use React + TypeScript strictly; avoid `any` unless justified.
- Use reusable components and a consistent spacing/type/color system.
- Use accessible labels, keyboard focus states, semantic HTML, and appropriate contrast.
- Keep animations subtle and respect reduced-motion preferences.
- Do not invent meeting counts, question completion, answer accuracy, or memory metrics in the UI. If data is not yet available, show an explicit empty/not-yet-available state.
- Use TanStack Query for health/readiness fetching, with sensible refetch intervals and error handling.
- Use React Router for page routing, even if Phase 1 has only the overview route.

## 7. Docker and local developer experience

Create a local Docker Compose setup for:
- PostgreSQL 16 with persistent named volume and health check.
- Backend API.
- Frontend development or production-preview service, choosing a maintainable setup and documenting it.

Requirements:
- Pin major versions and use reproducible dependency manifests/lockfiles where practical.
- Use environment variables; do not hardcode credentials in compose files.
- Add `.dockerignore` files where appropriate.
- Add a non-root runtime user in production Docker images where practical.
- Ensure service startup waits for database health, not merely container start.
- Keep raw source data out of Docker build contexts when not needed.
- Provide commands for local non-Docker development as well as Docker Compose.
- Do not require cloud hosting, paid services, or external databases for local development.

## 8. Documentation — required deliverables in this phase

Create and maintain documentation outside `docs/prompts/` as well as the prompt index.

### Root documentation
1. `README.md`: project purpose, key capabilities, architecture summary, prerequisites, setup, run commands, tests, environment setup, troubleshooting, and current phase status.
2. `.env.example`: documented safe environment variables.

### Technical documentation under `docs/`
1. `00_PROJECT_OVERVIEW.md`: problem, users, scope, non-goals, assessment deliverables, success criteria.
2. `01_REQUIREMENTS_SPECIFICATION.md`: functional/non-functional requirements mapped to the Catalist brief.
3. `02_SYSTEM_ARCHITECTURE.md`: component boundaries, data flow, deployment view, and Mermaid diagrams.
4. `03_DATA_AND_MEMORY_DESIGN.md`: transcript source-of-truth principle, speaker-turn evidence unit, short-term vs long-term memory concepts, temporal memory approach, and future schema plan. Clearly mark future-phase design vs implemented features.
5. `04_RETRIEVAL_AND_AGENT_DESIGN.md`: future hybrid retrieval and LangGraph research flow; bounded context and cross-meeting retrieval requirements.
6. `05_CITATION_AND_EVIDENCE_POLICY.md`: exact quote rules, citation structure, deterministic validation requirements, and provenance policy.
7. `06_API_CONTRACT.md`: Phase 1 implemented health/readiness endpoints and planned API surface clearly separated.
8. `07_TESTING_AND_EVALUATION_PLAN.md`: test layers, acceptance gates, 25 supplied questions, 10 independently authored questions, manual verification, metrics, and failure analysis.
9. `08_SECURITY_AND_PRIVACY.md`: secret handling, CORS, logging redaction, dataset handling, provider privacy, and local-only mode.
10. `09_DEPLOYMENT_AND_OPERATIONS.md`: local setup, Docker Compose, migrations, logs, health checks, backup considerations, and future deployment considerations.
11. `10_PHASE_TRACKER.md`: all phases, status, dependencies, acceptance criteria summary, and links to each phase prompt.

### Documentation subfolders
- `docs/architecture/`: Mermaid source diagrams for system context, container/component architecture, and initial runtime sequence.
- `docs/decisions/`: ADRs with context, decision, alternatives, consequences. Create at least:
  - `ADR-001-modular-monolith.md`
  - `ADR-002-postgresql-pgvector.md`
  - `ADR-003-local-first-model-strategy.md`
  - `ADR-004-langgraph-and-langsmith.md`
  - `ADR-005-exact-evidence-validation.md`
- `docs/api/`: endpoint examples or OpenAPI usage notes.
- `docs/database/`: initial database setup and migration notes.
- `docs/operations/`: local runbook and troubleshooting.
- `docs/evaluation/`: evaluation protocol and templates for ground-truth review/failure log.

### Prompt documentation
- `docs/prompts/README.md`: prompt index, execution order, prerequisite checks, and rule that each phase is run and accepted separately.
- `docs/prompts/PHASE_01_FOUNDATION.md`: save this complete prompt in the repository.
- Ensure the Phase 2 prompt file remains present if already supplied. Update the prompt index to link to it and mark it Ready only if the file is actually present.
- List later phase prompt files as Planned until they are written. Do not create empty prompt files just to make the tree look complete.

Every document must distinguish **implemented now**, **designed for later**, and **not in scope**. Keep documentation consistent with the actual code. Avoid claiming a feature is complete when only a design exists.

## 9. Testing and quality gates

### Backend tests
- Application imports and starts in test mode.
- Health endpoint returns expected status and project metadata.
- Readiness endpoint correctly reports database availability.
- Request ID is generated when absent and propagated when valid.
- CORS configuration is loaded from settings.
- Invalid configuration produces a clear startup error.
- LangSmith disabled/no-key mode does not break startup.
- Database session dependency can be overridden in tests.

### Frontend tests
- Overview page renders product name and workflow.
- API status component renders loading, healthy, and unavailable states.
- Query error is handled without crashing the app.
- Basic navigation works.

### Static checks
- Backend lint/format check.
- Frontend TypeScript typecheck and production build.
- Docker Compose configuration validation.
- Alembic migration upgrade against the local/test PostgreSQL database.

Do not mark a test as passed unless it was actually run. If Docker or a required service is unavailable, state the exact blocked check and provide the command needed to run it.

## 10. Acceptance criteria — Phase 1 is complete only when

- [ ] Existing repository and source materials were inspected before implementation.
- [ ] Backend and frontend have clear, maintainable project structures.
- [ ] Backend starts and health endpoint works.
- [ ] Readiness endpoint accurately checks PostgreSQL.
- [ ] PostgreSQL 16 starts through Docker Compose with persistent storage and health check.
- [ ] Alembic is configured and baseline migration succeeds.
- [ ] pgvector extension is available/enabled for later use.
- [ ] Typed settings and `.env.example` are complete.
- [ ] Request ID middleware, centralized errors, and structured logs work.
- [ ] LangSmith can be enabled by configuration and is optional without credentials.
- [ ] Frontend runs and displays real backend/database status.
- [ ] Frontend typecheck and production build pass.
- [ ] Backend tests pass.
- [ ] Docker Compose config validates.
- [ ] All required documentation files are written and match implementation status.
- [ ] Phase 1 prompt is saved under `docs/prompts/` and prompt index is updated.
- [ ] No paid API key is required for the foundation to run.
- [ ] No transcript ingestion or later-phase agent functionality has been prematurely implemented.

## 11. Final report required from you

When implementation is complete, provide a concise but precise report containing:

1. Summary of what was implemented.
2. Final repository tree (relevant files only).
3. Commands to run backend, frontend, database, and migrations.
4. Tests/checks actually executed and their results.
5. Any blocked checks and why.
6. Environment variables the developer must configure.
7. Documentation and ADR files created.
8. Deviations from the technical specification and why.
9. Acceptance checklist with each item marked PASS, FAIL, or BLOCKED and evidence.
10. Confirmation that Phase 2 can begin, or the exact blockers that must be fixed first.

Do not begin Phase 2 automatically. Stop after Phase 1 and wait for review and acceptance.

---

## Developer completion checklist

Use this after Antigravity finishes:

- [ ] Review generated code and docs rather than trusting the completion summary.
- [ ] Run the documented backend and frontend commands independently.
- [ ] Confirm PostgreSQL persistence survives container restart.
- [ ] Confirm secrets are absent from Git status and tracked files.
- [ ] Confirm docs distinguish designed vs implemented features.
- [ ] Confirm no Phase 2 ingestion work has leaked into Phase 1.
- [ ] Accept Phase 1 only when every required acceptance criterion passes or a documented, explicitly accepted exception exists.
