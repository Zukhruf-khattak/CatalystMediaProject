# ADR-004: LangGraph Multi-Agent Architecture and LangSmith Observability

## Status
Accepted

## Context
The Catalist build test evaluation requires:
1. Multi-step research across meetings (identifying initial proposals, finding intermediate debates, resolving final decisions or compromises).
2. Explicit temporal navigation across meeting series (meetings a -> b -> c -> d).
3. Stateful execution with checkpoints, loop limits, and observable traces.
4. Tracing and debugging observability without hard dependency on paid credentials.

## Decision
1. **LangGraph for Stateful Multi-Step Orchestration (Phase 5+)**:
   - Represents the research process as a directed state graph with typed state, checkpointing, and branch decisions.
   - Separation of concerns: Model decides search query strategy, tool arguments, and synthesis; deterministic code enforces citation validation, query bounds, and cycle limits.
2. **LangSmith Integration for Developer Tracing**:
   - Integrated strictly via standard environment variables (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT`).
   - If credentials are absent or `LANGSMITH_TRACING=false`, the system logs that tracing is disabled and continues normally without error.
   - Privacy & Redaction Policy: Full meeting transcripts and raw PII are never pushed to external tracing endpoints. Only query metadata, tool invocation signatures, and node execution times are exported.

## Alternatives Considered
1. **Single-Prompt Zero-Shot / RAG**:
   - *Cons*: Cannot handle cross-meeting temporal changes or multi-hop contradictions; fails the core assessment criteria ("Real agent behaviour: retrieve, loop, process in steps").
2. **Custom Loop without Framework**:
   - *Cons*: High engineering overhead for state persistence, serialization, and visual inspection; difficult for external evaluators to observe agent states.

## Consequences
- **Positive**: Clean state management, human-in-the-loop review potential, graph inspection, zero startup penalty when unconfigured.
- **Phase 1 Scope**: Configuration, logging hooks, and graceful degradation implemented; graph nodes and execution deferred to Phase 5.

