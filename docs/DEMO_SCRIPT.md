# Catalist Meeting Intelligence Agent: 3–5 Minute Live Demo Script

**Audience**: Technical Evaluators, Engineering Leadership, Stakeholders  
**Duration**: 3–5 Minutes  
**Prerequisites**: Backend running at `http://localhost:8000`, Frontend running at `http://localhost:5173`.  
**Database**: `data/processed/catalist.db` (138 meetings ingested, 48,148 turns with embeddings).

---

## Act 1: Executive Overview & Ingestion Scale (0:00 – 1:00)

### Visual: Dashboard Overview (`/`) & Ingestion Monitor (`/ingestion`)
1. **Navigate to the Ingestion Dashboard** (`http://localhost:5173/ingestion`):
   - Highlight the **Corpus Statistics** cards:
     - **Total Meetings**: 138 (100% of AMI corpus across 35 design teams).
     - **Speaker Turns**: 48,148 turns parsed and embedded.
     - **Corpus Words**: 676,745 words (~880,000 tokens).
     - **Vector Embeddings**: 48,148 dense vectors (384-dim `all-MiniLM-L6-v2`) generated on local CPU in 18.7 minutes (~42.8 turns/sec).
2. **Talking Points**:
   > *"Welcome to the Catalist Meeting Intelligence Agent. Rather than passing 880,000 tokens into an LLM window, Catalist structures meeting history into an append-only temporal memory graph backed by dual lexical and dense vector indices. Everything runs local-first with zero paid API keys."*

---

## Act 2: Multi-Meeting Research Agent & Citation Validation (1:00 – 2:30)

### Visual: Research Assistant (`/research`)
1. **Select Question Q01 Pill (Team TS3006)**:
   - Query: *"Team TS3006 planned both an LCD screen and speech recognition. When the costs forced a cut, which of the two did they drop, which did they keep, and what reason was given for keeping it?"*
2. **Click "Research Question"**:
   - Observe the **Live LangGraph Stepper**:
     - `Input Validation` -> `Query Analysis` (Identified Team `TS3006`, entities: LCD, speech recognition) -> `Retrieval Planning` -> `Tool Execution` -> `Evidence Assessment` -> `Answer Generation` -> `Citation Validation`.
3. **Inspect the Answer & Badges**:
   - Point out the **Validation Status**: `PASSED` badge.
   - Point out the **Answer Structure**: Exactly 2 plain sentences.
   - Point out the **Citations**: 2 citations spanning 2 distinct meetings:
     - `TS3006b` (Turn 118, Speaker A): Quote verifying initial plan for LCD screen and speech recognition.
     - `TS3006d` (Turn 241, Speaker A): Quote verifying that dropping LCD would require too many extra buttons.
4. **Click "Inspect Turn Context"**:
   - Opens the `CitationContextModal` displaying the target turn highlighted with ±2 surrounding speaker turns in chronological sequence.
5. **Talking Points**:
   > *"Catalist enforces a deterministic validation boundary. Quotations must be verbatim extracts of $\ge 6$ words from a single speaker turn, and every answer must cite at least two distinct meetings of the target team. Paraphrases or single-meeting answers are automatically rejected."*

---

## Act 3: Temporal Memory & Decision Lineage (2:30 – 3:30)

### Visual: Temporal Memory Explorer (`/memory`) & Decision Timeline (`/decisions`)
1. **Navigate to the Decision Timeline** (`http://localhost:5173/decisions`):
   - Select Team **TS3011** or **TS3007**.
   - Show how the power source evolved chronologically:
     - *Meeting C*: Battery + kinetic energy / solar cells selected.
     - *Meeting D*: Kinetic/solar components eliminated due to 12.50 Euro budget limits.
   - Show the visual diff showing the old decision marked `SUPERSEDED` and the final decision marked `CURRENT`.
2. **Navigate to Memory Explorer** (`/memory`):
   - Filter by `MemoryType: DECISION` and `Status: SUPERSEDED`.
   - Show that historical decisions are never overwritten or deleted; they form an immutable, auditable lineage connected by `updates` relationships.
3. **Talking Points**:
   > *"Enterprise projects don't make decisions in a vacuum. By preserving historical decisions in an append-only graph, Catalist understands not just where a project ended up, but every trade-off, cost cut, and revision along the way."*

---

## Act 4: Team TS3012 Pre-Meeting Briefing (3:30 – 4:30)

### Visual: Pre-Meeting Briefing (`/briefing`)
1. **Navigate to Pre-Meeting Briefing** (`http://localhost:5173/briefing`):
   - Note the **Target Meeting**: `TS3012d` (Final Product Integration).
   - Walk through the **9 Standard Sections**:
     - *1. Team Coverage*: Audited 3 meetings (TS3012a, b, c) with speaker roles.
     - *2. Executive Summary*: 25 Euro retail price target, spongy rubber casing.
     - *3. Meeting Timeline*: Chronological discussion progression.
     - *4. Current Decisions*: Basic battery, 25 Euro retail price target.
     - *5. Decision Changes*: Evolution log.
     - *6. Open Actions & Owners*: Explicitly tracked action items.
     - *7. Unresolved Disagreements*: Removable fruit cover vs. fixed rubber casing dispute between Speaker D and Speaker A.
     - *8. Items Requiring Attention*: Prioritized checklist for the upcoming meeting.
     - *9. Evidence & Limitations*: Transparent disclosure of off-record activities and attribution certainty.
2. **Click "Regenerate Briefing"**:
   - Triggers live generation, updating from Version 1 to Version 2 with verified citations.

---

## Act 5: Submission Deliverables & CLI Demonstration (4:30 – 5:00)

### Visual: Terminal / Artifacts Inspection
1. **Show Generated Artifacts**:
   ```bash
   dir artifacts/
   ```
   - `artifacts/answers.json`: All 25 benchmark answers + cited brief (100% deterministic validation pass).
   - `artifacts/briefing.md`: Complete TS3012 briefing.
   - `artifacts/evaluation_report.md`: Custom 10-query capability benchmark + 10k scaling analysis.
   - `technical_report.md`: High-density architectural and empirical report.
2. **Run Quick CLI Ask Demo**:
   ```bash
   python -m app.cli ask "Team TS3006 planned both an LCD screen and speech recognition. When the costs forced a cut, which of the two did they drop?" --team TS3006
   ```
3. **Closing Statement**:
   > *"In summary, Catalist delivers complete corpus persistence, stateful agentic reasoning, deterministic evidence validation, and automated executive intelligence—engineered from the ground up for production scale."*

