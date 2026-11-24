# Catalist Meeting Intelligence: Technical Interview Defense Guide

This guide prepares you for deep technical interview questions about the internal design, trade-offs, and architecture of the Catalist Meeting Intelligence Agent.

---

## Question 1: Why did you choose hybrid retrieval instead of vector search alone?

### Core Answer:
Vector search is excellent at fuzzy semantic similarity, but it has severe failure modes in multi-meeting enterprise transcripts:
1. **Semantic Dilution on Common Vocabulary**: In product design meetings, domain words like *"remote"*, *"television"*, or *"battery"* appear thousands of times. A vector query for *"Did they want a remote for television only?"* yields low discriminative contrast across thousands of turns because every turn discusses TV remotes.
2. **Loss of Exact Numerical Tokens**: Embeddings often fail to distinguish exact figures (e.g. *12.50 Euros* vs *15.50 Euros*, or *Turn 238* vs *Turn 245*).
3. **Out-of-Vocabulary Jargon & Codes**: Meeting codes (`TS3006d`), component acronyms (`L_C_D_`, `P_C_B_`, `R_S_I_`), and speaker labels (`Speaker A`) require exact keyword matching.

### Architectural Solution:
We combine **Dense Vector Search** (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) with **Lexical Keyword Search** (SQLite FTS5 / PostgreSQL `tsvector` with BM25 ranking) via **Reciprocal Rank Fusion (RRF)**:
$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{lexical}\}} \frac{w_m}{k + \text{rank}_m(d)} \quad (k = 60, w_{\text{dense}}=0.6, w_{\text{lex}}=0.4)$$
Lexical BM25 pins down exact component names, numbers, and meeting codes, while dense embeddings capture conceptual intent and synonyms.

---

## Question 2: How does your temporal memory identify a superseded decision?

### Core Answer:
Temporal memory does not simply overwrite old database records. It treats meeting memory as an **append-only, immutable graph**:
1. **Meeting Sequence Ordering**: Every meeting has a chronological stage (`a` $\to$ `b` $\to$ `c` $\to$ `d`) and ordinal sequence index.
2. **Topic & Constraint Anchors**: When a new decision is extracted in Meeting C (e.g., *"Power source: battery only"*), the `TemporalReasoningService` queries existing active decisions for that team with matching facet tags (`category: power_source`).
3. **Contradiction & Evolution Detection**:
   - If the new statement contradicts or modifies an active decision from an earlier meeting (e.g., Meeting B had *"Power source: battery + kinetic dynamo"*), the system creates a directed `MemoryRelationship` of type `updates`.
   - The older record's lifecycle status is transitioned from `CURRENT` $\to$ `SUPERSEDED`, and `superseded_by_id` is populated.
   - The new record is inserted with status `CURRENT`.
4. **Audit Trail**: Historical decisions remain permanently in the database with their original meeting context, turn ID, and verbatim quotes intact, allowing the system to reconstruct decision timelines ($a \to b \to c \to d$).

---

## Question 3: How does LangGraph decide when to retrieve more evidence?

### Core Answer:
In `backend/app/agent/graph.py`, the research agent uses an explicit **state graph with conditional routing** rather than an open-ended loop:
1. **`query_analysis` Node**: Parses the query into required facets (target team, entities, temporal stages, constraint dimensions).
2. **`retrieval_planning` & `tool_execution` Nodes**: Fetches hybrid evidence packs and temporal memory records.
3. **`evidence_assessment` Node (Decision Point)**:
   - Evaluates whether the retrieved evidence covers **all required facets** AND satisfies the Catalist multi-meeting rule ($\ge 2$ distinct meetings).
   - If missing facets remain (e.g., found the initial decision in Meeting B, but missing the final budget cut in Meeting D), the node sets `is_sufficient = False` and populates `missing_facets`.
   - The conditional router `route_after_evidence_assessment` checks:
     - If `missing_facets` exists AND `iteration < max_iterations (2)`: loops back to `retrieval_planning` with a refined query targeting the missing meeting stages.
     - If iterations are exhausted: routes to `final_response` with explicit disclosure of partial evidence.
     - If `is_sufficient = True`: advances to `answer_generation`.

---

## Question 4: How do you guarantee that a citation is an exact transcript quotation?

### Core Answer:
We do **not** trust LLMs to verify their own citations. Verification is delegated to `CitationValidationService`—a deterministic Python/SQL service operating outside the LLM:
1. **Verbatim Substring Matching**:
   The candidate quote is normalized (case-insensitive, whitespace collapsed, punctuation stripped) and checked as a literal substring against the stored `raw_text` of the claimed `meeting_id` and `turn_id`. Paraphrases fail immediately.
2. **Single Speaker-Turn Boundary**:
   The quotation must originate from **one single speaker turn**. Stitching quotes across multiple turns or conversations is strictly rejected.
3. **Minimum Length Guardrail**:
   Every quotation must contain $\ge 6$ whitespace-delimited words to prevent trivial one-word matches.
4. **Speaker Attribution & Role Verification**:
   Speaker letter (A, B, C, D) is verified against the turn's speaker record. Roles (*Project Manager*, *Industrial Designer*) are accepted only if recorded in transcript metadata.
5. **Substantive Claim Overlap ($\ge 20\%$)**:
   The validator calculates token overlap between the answer's non-stopword content tokens and the citation quotations. Answers introducing unsupported claims fail validation.

---

## Question 5: What happens when two meetings contain contradictory information?

### Core Answer:
Contradiction is a natural feature of meeting intelligence (teams change their minds or disagree):
1. **Within the Same Team Across Time**:
   This is treated as **temporal evolution**. The earlier meeting represents the initial proposal; the later meeting represents a revision or supersession. The agent explicitly articulates both points in time:
   - *Example (Q04 / TS3011)*: *"Team TS3011 chose a hybrid energy combination of a battery with solar cells in meeting TS3011c, but dropped solar cells in meeting TS3011d to fit the 12.50 Euro budget limit."*
2. **Within the Same Meeting Between Speakers**:
   This is captured as an `UNRESOLVED` disagreement under `MemoryType.DISAGREEMENT`:
   - Both competing positions and speakers are indexed (e.g., Speaker D pushing for removable fruit covers vs. Speaker A objecting due to tooling complexity).
   - The briefing generator highlights this in **Section 7: Unresolved Disagreements** as an agenda item requiring resolution in the upcoming meeting.
3. **Ambiguity Preservation**:
   If evidence does not clearly indicate whether an earlier stance was formally overruled, the memory record sets `is_ambiguous = True` without forcing an artificial resolution.

---

## Question 6: How would you handle 10,000 meetings without slowing down retrieval?

### Core Answer:
Scaling from 138 meetings (~48k turns) to 10,000 meetings (~3.5M turns) requires architectural shifts from our local prototype:

1. **Storage & Database (ADR-002)**:
   - Transition from SQLite BLOBs to **PostgreSQL 16 with `pgvector`**.
   - Partition the `transcript_turns` table using **declarative range/list partitioning** by `team_id` and date range. A query targeting Team TS3012 scans $< 50,000$ rows rather than 3.5 million.
2. **Vector Indexing (HNSW)**:
   - Replace flat cosine scans with **Hierarchical Navigable Small World (HNSW)** indexing:
     `CREATE INDEX ON transcript_turns USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);`
   - Keeps nearest-neighbor retrieval latency under **25 ms** across millions of vectors.
3. **Distributed Asynchronous Ingestion**:
   - Ingestion takes ~23 hours on single-thread CPU. We decouple ingestion into a distributed pipeline using **Celery / RabbitMQ** worker pods.
   - Batch vector embeddings on GPU instances (NVIDIA T4 / A10G processing ~2,000 turns/sec), completing 10,000 meetings in **under 35 minutes**.
4. **Caching & Materialized Lineage**:
   - Materialize transitive closure paths for temporal supersession trees to avoid recursive SQL joins.
   - Cache active `CURRENT` decisions per team in **Redis** with write-through invalidation upon memory updates.
