# Frontend Component Architecture

## 1. Executive Summary

The Catalist Meeting Intelligence Frontend (Phase 8) is an enterprise-grade, responsive Single Page Application (SPA) built with React 18, TypeScript 5, Vite 5, Tailwind CSS, and TanStack Query. It provides intuitive, real-time access to the autonomous meeting intelligence platform, connecting directly to FastAPI backend services without mock data.

The frontend is engineered to explore 138 AMI meeting transcripts, inspect verified atomic temporal memories, visualize multi-meeting decision morphing across chronological sequences ($a \to b \to c \to d$), stream multi-step LangGraph agent execution stages via Server-Sent Events (SSE), and examine deterministic transcript turn evidence with surrounding dialogue context.

---

## 2. Technology Stack & Design System

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Core Framework** | React + React DOM | `18.3.1` | Concurrent rendering, hooks, component lifecycle |
| **Language** | TypeScript | `5.6.3` | Strict type checking (`noUnusedLocals`, `strict: true`) |
| **Bundler & Tooling** | Vite | `5.4.8` | Lightning fast HMR and optimized Rollup production bundling |
| **Routing** | React Router DOM | `6.27.0` | Client-side routing, parameter handling, and redirects |
| **Data Fetching & Cache** | TanStack React Query | `5.59.0` | Server state caching, background refetching, query status |
| **Forms & Validation** | React Hook Form + Zod | `7.92.0` / `4.6.7` | Uncontrolled typed form inputs with schema validation |
| **Styling** | Tailwind CSS | `3.4.13` | Utility-first styling with dark theme design tokens |
| **Iconography** | Lucide React | `0.453.0` | Consistent, accessible iconography |
| **Testing** | Vitest + React Testing Library | `2.1.3` / `16.0.1` | Unit and integration component test suites |

---

## 3. Application Routing & Page Architecture

```
                    ┌─────────────────────────┐
                    │      BrowserRouter      │
                    │   (QueryClientProvider) │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │       Main Layout       │
                    │  (Header + Sidebar Nav) │
                    └────────────┬────────────┘
                                 │
     ┌──────────────┬────────────┼────────────┬──────────────┐
     │              │            │            │              │
┌────▼────┐    ┌────▼────┐  ┌────▼────┐  ┌────▼────┐   ┌─────▼─────┐
│Overview │    │Research │  │Citation │  │ Memory  │   │ Decision  │
│  Page   │    │Assistant│  │ Viewer  │  │Explorer │   │ Timeline  │
│   (/)   │    │(/research│  │(/citations│ │(/memory)│  │(/decisions)│
└─────────┘    └─────────┘  └─────────┘  └─────────┘   └───────────┘
                    │            │            │              │
               ┌────▼────┐  ┌────▼────┐       │              │
               │ Briefing│  │Ingestion│       │              │
               │  Page   │  │ Monitor │       │              │
               │(/briefing│ │(/ingestion│      │              │
               └─────────┘  └─────────┘       │              │
                    │                         │              │
               ┌────▼────┐                    │              │
               │Evaluation│                   │              │
               │Dashboard│                    │              │
               │(/eval...│                    │              │
               └─────────┘                    │              │
                    │                         │              │
                    └────────────┬────────────┘              │
                                 │                           │
                    ┌────────────▼───────────────────────────▼┐
                    │       CitationContextModal (Shared)     │
                    │  Inspect ±2 Surrounding Turns Context   │
                    └─────────────────────────────────────────┘
```

### Route Table & Capabilities

| Route | Primary Component | Backend API Endpoint | Key Capabilities |
|---|---|---|---|
| `/` | `OverviewPage` | `/api/v1/health`, `/api/v1/ready` | Operational metrics, 5-stage pipeline, quick launcher, Phase 1–9 roadmap. |
| `/research` | `ResearchAssistantPage` | `POST /api/v1/agent/query/stream`, `POST /api/v1/agent/query` | Natural language queries, benchmark pills, live SSE stage stepper, answer card, citations. |
| `/citations` | `CitationViewerPage` | `GET /api/v1/retrieval/turns/{id}` | UUID turn search, 6-rule validation checklist, curated exemplar quotes, turn context. |
| `/memory` | `MemoryExplorerPage` | `GET /api/v1/memory/search` | Multi-filter (team, type, status, lexical), relationships badges, turn context links. |
| `/decisions` | `DecisionTimelinePage` | `GET /api/v1/briefings/{team}/latest` | Sequential meeting timeline ($a \to b \to c \to d$), supersession before/after diffs, active decisions. |
| `/briefing` | `BriefingPage` | `GET /api/v1/briefings/ts3012`, `GET /api/v1/briefings/{team}/versions` | 9 executive sections, regeneration trigger, version selector, citation pills, raw Markdown copy. |
| `/ingestion` | `IngestionPage` | `GET /api/v1/ingestion/stats`, `GET /api/v1/ingestion/jobs` | Real-time corpus stats (138 meetings, 31.8k turns), job history table, launch ingestion job modal. |
| `/evaluation`| `EvaluationPage` | Phase 4/6/7 Empirical Telemetry | Measured metrics (Recall 82%, Precision 90%, Latency 97ms), modality table, 10k scaling roadmap. |

---

## 4. Key Feature Components

### 4.1. Research Assistant (`ResearchAssistantPage.tsx`)
- **Query Input & Zod Validation:** Validates query length $\ge 5$ characters with team auto-detection or override.
- **Curated Benchmark Pills:** 5 high-impact questions (Q01, Q02, Q03, Q07, Q11) for one-click testing.
- **Server-Sent Events (SSE) Stepper:** Real-time visual progress across 8 LangGraph nodes (`input_validation` $\to$ `query_analysis` $\to$ `retrieval_planning` $\to$ `tool_execution` $\to$ `evidence_assessment` $\to$ `answer_generation` $\to$ `citation_validation` $\to$ `final_response`).
- **Deterministic Citation Badges:** Displays validation status (`PASSED` vs `FAILED`), loop iteration count, supporting meeting codes, and interactive context triggers.

### 4.2. Citation Context Inspector (`CitationContextModal.tsx`)
- Shared modal component invoked across Research, Briefings, Memory, and Timeline pages.
- Invokes `GET /api/v1/retrieval/turns/{turn_id}` to retrieve the exact target turn plus 2 preceding and 2 succeeding speaker turns from PostgreSQL.
- Highlights target turn with a high-contrast indigo border and "Target Cited Turn" badge, showing exact timestamps and verified speaker labels/roles.

### 4.3. Team TS3012 Pre-Meeting Briefing (`BriefingPage.tsx`)
- Renders all 9 mandated sections:
  1. Executive Summary
  2. Meeting Coverage ($TS3012a, b, c$)
  3. Current Confirmed Decisions
  4. Decision Evolution & Changes (Before $\to$ After supersession diffs)
  5. Open Actions & Commitments (Owner assignment & confidence level)
  6. Unresolved Disagreements (Friction points, competing positions)
  7. Confirmed Product Requirements
  8. Key Technical Specifications & Entities
  9. Full Raw Markdown document with one-click clipboard copying.
- Supports on-demand briefing regeneration and historical version switching.

---

## 5. State Management & API Communication

- **Network Client (`frontend/src/lib/api.ts`):** Centralized, typed API layer abstracting HTTP `fetch` and SSE streams.
- **Server-Sent Events Consumer:** Uses native `ReadableStream` reader and `TextDecoder` to parse `event: stage`, `event: final`, and `event: error` payloads with automatic chunk buffering.
- **TanStack React Query:** Used for caching readiness, health, and ingestion telemetry.
- **Component Local State (`useState` / `useForm`):** Manages user inputs, filters, active modal overlays, and view toggles.

---

## 6. Testing & Quality Assurance

- **Vitest & React Testing Library:** 10 test suites covering all 8 routes and shared modal inspectors.
- **Strict TypeScript Validation:** Zero TypeScript compiler warnings or errors (`tsc --noEmit`).
- **Deterministic Mocking:** All backend API contracts mocked using strongly-typed Pydantic-equivalent TypeScript interfaces.
