# Phase 8: React Frontend Implementation

Act as a senior frontend engineer working with an AI backend team.

Implement **Phase 8: React Frontend** in the existing Catalist Meeting Intelligence project.

First inspect the repository, existing Phase 1–7 implementation, FastAPI endpoints, Pydantic schemas, and API contracts. Build on the existing backend. Do not duplicate backend functionality or create mock data to represent completed features.

## Objective

Build a polished, responsive React application that allows users to explore meeting intelligence, ask research questions, inspect citations, explore temporal memory, and view the TS3012 briefing.

## 1. Technology Stack

Use the existing frontend architecture:

- React + TypeScript.
- Vite.
- Tailwind CSS.
- shadcn/ui and Radix UI.
- Lucide React icons.
- React Router.
- TanStack Query.
- React Hook Form + Zod.

Keep components reusable, typed, and organized by feature.

## 2. Application Layout

Build a professional dashboard with:

- Responsive sidebar navigation.
- Top navigation/header.
- Main content area.
- Consistent typography, spacing, and color system.
- Loading, error, empty, and success states.
- Responsive layouts for desktop and smaller screens.

Create these main routes:

1. Overview Dashboard
2. Research Assistant
3. Citation Viewer
4. Memory Explorer
5. Decision Timeline
6. TS3012 Briefing
7. Ingestion Status
8. Evaluation Dashboard

## 3. Overview Dashboard

Display backend-derived information:

- Total meetings ingested.
- Teams and transcript segments.
- Memory records.
- Ingestion status.
- Recent research activity, if available.
- Quick access to the research assistant and TS3012 briefing.

Use actual API data. Clearly distinguish unavailable information from zero values.

## 4. Research Assistant

Build the main question-answering interface.

Requirements:

- Natural-language question input.
- Team selection or filtering where supported by the API.
- Submit and display agent responses.
- Stream progress using the existing SSE endpoint.
- Show useful execution stages such as query analysis, retrieval, evidence assessment, and answer generation when the backend exposes them.
- Display insufficient-evidence and error responses clearly.
- Preserve conversation/session context where supported.

Do not simulate agent progress or invent backend events.

## 5. Citation Viewer

Display citations alongside answers.

Each citation should show:

- Meeting ID.
- Speaker label.
- Exact transcript quotation.
- Source reference.
- Validation status, when returned by the API.

Allow users to open a citation and inspect its original transcript turn and surrounding context.

Make the relationship between answer claims and supporting evidence clear.

## 6. Memory Explorer

Build an interface to browse persisted temporal memories.

Include:

- Search.
- Team filtering.
- Meeting filtering.
- Memory type filtering.
- Status filtering.
- Memory detail view.
- Supporting transcript evidence.
- Related memory relationships.

Show current, superseded, open, resolved, and rejected states using consistent visual indicators.

## 7. Decision Timeline

Display decisions chronologically.

Show:

- Original decisions.
- Updated decisions.
- Superseded decisions.
- Supporting meeting references.
- Evidence for each change.

Make decision history understandable without hiding earlier decisions.

## 8. TS3012 Briefing

Create a dedicated briefing page.

Display the generated briefing with sections for:

- Executive summary.
- Meeting timeline.
- Current decisions.
- Decision changes.
- Open actions and owners.
- Unresolved disagreements.
- Items requiring attention.
- Evidence and coverage limitations.

Render citations as interactive references that open the corresponding transcript evidence.

Provide a regenerate action only if the backend exposes it.

## 9. Ingestion and Evaluation Views

**Ingestion Status:**
- Display ingestion runs and processing status.
- Show discovered, processed, skipped, and failed counts when available.
- Display errors and progress from the backend.

**Evaluation Dashboard:**
- Display available retrieval and answer-quality metrics.
- Show evaluation results and failure cases.
- Clearly distinguish measured results from unavailable metrics.

Do not fabricate charts or performance numbers.

## 10. API Integration

Create a centralized, typed API client.

Requirements:

- Use existing FastAPI routes and response schemas.
- Configure the backend URL through environment variables.
- Use TanStack Query for server-state management.
- Handle loading, errors, retries, and cache invalidation.
- Implement SSE handling according to the actual backend event format.
- Validate frontend forms with Zod.
- Keep API logic separate from UI components.

Never connect the frontend directly to PostgreSQL.

## 11. Testing

Add frontend tests using Vitest and React Testing Library.

Test:

- Route rendering.
- Research form validation.
- API loading and error states.
- SSE event handling.
- Citation display and navigation.
- Memory filters.
- Decision timeline rendering.
- Briefing rendering.
- Ingestion status.
- Responsive navigation.

Run a complete frontend build and resolve TypeScript errors.

## 12. Documentation

Update:

- `docs/02_SYSTEM_ARCHITECTURE.md`
- `docs/12_API_DOCUMENTATION.md`
- `docs/13_FRONTEND_ARCHITECTURE.md`
- `docs/14_OBSERVABILITY.md`
- `docs/17_TESTING_STRATEGY.md`
- `docs/18_DEPLOYMENT_GUIDE.md`
- `docs/20_KNOWN_LIMITATIONS.md`

Add:

- `docs/architecture/FRONTEND_COMPONENT_ARCHITECTURE.md`
- `docs/operations/FRONTEND_RUNBOOK.md`

Save this prompt in:

`docs/prompts/PHASE_08_REACT_FRONTEND.md`

Update `docs/prompts/README.md`.

## Acceptance Criteria

- All required application routes work.
- Frontend uses real backend APIs.
- Research questions can be submitted and responses displayed.
- SSE progress works with the actual backend event format.
- Citations open their correct transcript evidence.
- Memory filters and decision timeline work.
- TS3012 briefing renders correctly.
- Ingestion and evaluation data are displayed accurately.
- Loading, error, and empty states are implemented.
- Responsive layout works.
- Frontend tests pass.
- Production build succeeds.
- Existing Phase 1–7 backend functionality remains operational.
- Documentation reflects the implementation.

Do not implement the final evaluation and submission package in this phase. That belongs to Phase 9.

At completion, report implemented routes, components, API integrations, test results, build results, commands to run, and known limitations.

**Stop after Phase 8 and wait for review.**

