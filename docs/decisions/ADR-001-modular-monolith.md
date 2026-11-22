# ADR-001: Modular Monolith Architecture Pattern

## Status
Accepted

## Context
The Catalist Meeting Intelligence Agent needs to ingest 138 AMI transcripts (~676,000 words), provide hybrid retrieval, maintain temporal memory across meeting sequences (meetings a through d), execute multi-step research via LangGraph, perform deterministic quote validation, generate pre-meeting briefs for Team TS3012, and scale architecturally towards a 10,000-meeting corpus.

The development environment is a single engineer setup, possibly running on limited RAM without GPU/CUDA. We must choose between microservices, serverless functions, or a modular monolith.

## Decision
We adopt a **Modular Monolith** architecture implemented in Python 3.12 with FastAPI for the backend, coupled to a React/TypeScript frontend.

The backend is structured into distinct, cohesive layers:
- `core/`: System configuration, logging, exceptions, middleware, and tracing hooks.
- `db/`: Engine, session lifecycle, and declarative base.
- `models/`: Domain entities and SQLAlchemy ORM models.
- `schemas/`: Pydantic v2 data validation and serialization contracts.
- `services/`: Encapsulated domain logic (ingestion, retrieval, memory, reasoning, citation validation).
- `api/v1/`: Thin route controllers that delegate strictly to services.

## Alternatives Considered
1. **Microservices (Separate Ingestion, Search, and Agent Services)**:
   - *Cons*: High deployment complexity, network overhead between services, distributed transaction challenges, heavy memory footprint incompatible with low-RAM developer machines.
2. **Serverless / Lambda Functions**:
   - *Cons*: Local development friction, cold starts, awkward stateful agent loops, difficult Docker-based local evaluation.

## Consequences
- **Positive**: Single codebase, straightforward local execution, atomic database transactions, zero network latency between ingestion and reasoning modules, fast testing and debugging.
- **Negative**: Requires strict discipline to keep boundaries clean; routes must not bypass service layers to access raw database sessions.
- **Phase 1 Scope**: Implemented foundation layers (`core`, `db`, `schemas`, `services`, `api/v1`), health and readiness endpoints. Domain modules for ingestion, memory, and agents remain interfaces for later phases.
