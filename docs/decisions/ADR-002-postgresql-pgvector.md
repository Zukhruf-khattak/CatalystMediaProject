# ADR-002: PostgreSQL 16 with pgvector and Hybrid Search

## Status
Accepted

## Context
The Catalist brief mandates querying a meeting corpus of 138 transcripts (scale target 10,000 meetings). Each question requires multi-meeting evidence across teams, exact keyword matches (e.g. specific component names like "LCD screen", "speech recognition", "curved case"), and semantic similarity queries.

We require a storage engine that supports:
1. Relational data (meetings, speaker turns, temporal sequences, teams, metadata).
2. Full-Text Search (lexical BM25/tsvector) for exact keyword matches.
3. Vector similarity search for semantic embeddings.
4. Transactional guarantees and persistence.

## Decision
We select **PostgreSQL 16** with the **pgvector** extension as the single unified persistence engine.

Key design points:
- Official Docker image: `pgvector/pgvector:pg16`.
- Lexical Search: PostgreSQL native `tsvector` with `tsquery` and GIN index on transcript turns.
- Semantic Search: `vector(384)` column on transcript chunks/turns indexed via HNSW or IVFFlat.
- Hybrid Retrieval: Reciprocal Rank Fusion (RRF) combining lexical and semantic score ranks inside PostgreSQL or backend service layer.

## Alternatives Considered
1. **Separate Vector Database (Pinecone, Qdrant, Chroma, Milvus) + Relational DB**:
   - *Cons*: Multi-database synchronization overhead, split-brain failure modes, external SaaS dependency or additional Docker container memory load, complex dual-query joins.
2. **Pure SQLite / Chroma**:
   - *Cons*: Poor concurrent write handling, limited full-text search capabilities across large corpora, does not reflect production architecture for a 10,000-meeting corpus.

## Consequences
- **Positive**: Single persistence engine, ACID transactions, atomic migrations via Alembic, zero cloud cost, local Docker container, scales easily to millions of turns.
- **Negative**: Requires pgvector extension installation (handled seamlessly by Docker `pgvector/pgvector:pg16` image).
- **Phase 1 Scope**: pgvector extension migration defined and ready in Alembic; health/readiness checks verify database connectivity. Domain tables are deferred to Phase 2.
