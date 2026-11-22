# ADR-003: Local-First and Free-Tier Model Strategy

## Status
Accepted

## Context
The Catalist build test evaluation requires:
1. Usability without mandatory paid API keys.
2. Lightweight CPU-compatible execution on local developer workstations with limited RAM (no CUDA or discrete GPU required).
3. Pluggable architecture allowing hosted providers when available (e.g. Gemini via free tier) or local models (Ollama).
4. No large model downloads during repository foundation setup.

## Decision
We enforce a **Local-First, Pluggable Model Strategy**:
- Provider configuration is driven entirely by environment variables (`LLM_PROVIDER`, `LLM_MODEL`, `OLLAMA_BASE_URL`, `GEMINI_API_KEY`).
- In Phase 1 foundation: No models are downloaded; no external API calls are made at startup.
- In Phase 2 ingestion: Local CPU-friendly embeddings (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) will be utilized for zero-cost, reproducible embeddings.
- In Phase 5 reasoning: Local Ollama (`llama3.2` or `mistral`) serves as the offline baseline, with hosted Gemini (`gemini-1.5-flash` / `gemini-2.0-flash`) as the zero-cost API alternative.

## Alternatives Considered
1. **Mandatory OpenAI / Anthropic APIs**:
   - *Cons*: Violates the requirement of zero paid API keys, breaks reproducible offline evaluation, costs money for evaluation test runs.
2. **Heavy Local LLM (70B or CUDA required)**:
   - *Cons*: Fails on consumer laptops with 8-16 GB RAM without dedicated GPUs.

## Consequences
- **Positive**: Anyone can clone, inspect, test, and run the project without paying for API tokens or owning specialized hardware.
- **Negative**: Smaller local models requires structured output constraints and deterministic fallback validators to prevent hallucinated quotes.
