# ADR-005: Exact Evidence Validation and Citation Engine

## Status
Accepted

## Context
The Catalist build test brief explicitly specifies:
- "Back every answer with one to three citations. A citation is a meeting id and a quote of at least six words copied exactly from that transcript, from within one speaker turn."
- "Quotes are checked automatically (case and spacing are ignored); paraphrases fail."
- "Tool-fit judgment: draw the line yourself between what a model decides and what plain code does, and defend it. Some of this work should never touch an LLM. Tell us which, and why the parts that do, do."

## Decision
We enforce a **Strict Model vs. Code Separation** for citations:
1. **Model Role**: Identify candidate evidence, synthesize coherent natural language answers to questions, and extract candidate verbatim excerpts.
2. **Code Role (Deterministic Validator)**:
   - Perform string verification against the authoritative transcript text in PostgreSQL.
   - Ignore whitespace variations and letter case, as permitted by the evaluation spec.
   - Verify that the quote contains at least six words.
   - Verify that the quote exists entirely within a single speaker turn in the specified `meeting_id`.
   - If the LLM generates a hallucinated or paraphrased quote, deterministic code rejects or aligns it against the closest exact speaker turn substring; it never relies on the model to "self-police" its quotes.

## Alternatives Considered
1. **LLM Self-Validation Prompt ("Are you sure this is verbatim?")**:
   - *Cons*: Highly unreliable, suffers from LLM confirmation bias, consumes extra tokens and latency, fails automatic grading.
2. **Fuzzy String Matching (Levenshtein distance > 0.8)**:
   - *Cons*: Fails the strict brief requirement: "Quotes are checked automatically (case and spacing are ignored); paraphrases fail."

## Consequences
- **Positive**: 100% adherence to assessment scoring rules, deterministic guarantees, zero hallucinated citations accepted into `answers.json`.
- **Phase 1 Scope**: Architectural boundary and policy established; validation service implementation scheduled for Phase 6.

