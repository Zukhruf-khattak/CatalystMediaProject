# Operational Runbook: LangGraph Research Agent

## 1. Overview

The Catalist Meeting Intelligence research agent provides stateful, multi-step question answering over cross-meeting transcripts and temporal memories. It is operable via the unified CLI (`catalist ask`) and REST API endpoints (`/api/v1/agent/*`).

---

## 2. CLI Operations

### 2.1 Basic Query
Submit a natural language question against the meeting archive:
```bash
python -m app.cli ask --query "Team TS3006 planned both an LCD screen and speech recognition. When costs forced a cut, which did they drop?"
```

### 2.2 Team-Scoped Query with Iteration Budget
Target a specific team and configure the retrieval loop limit:
```bash
python -m app.cli ask \
  --query "What casing material did Team ES2003 switch to in their final meeting?" \
  --team-code ES2003 \
  --max-iterations 3
```

### 2.3 Resuming a Conversational Session
Continue an existing dialogue using the persistent session UUID:
```bash
python -m app.cli ask \
  --query "Who first suggested this change?" \
  --session-id "550e8400-e29b-41d4-a716-446655440000"
```

---

## 3. REST API Operations

### 3.1 Single-Turn Question Answering
**Endpoint**: `POST /api/v1/agent/query`

**Request Payload**:
```json
{
  "question": "What colour scheme did Team TS3008 choose in the final meeting and why?",
  "team_code": "TS3008",
  "max_iterations": 2
}
```

**Response Payload (200 OK)**:
```json
{
  "question": "What colour scheme did Team TS3008 choose in the final meeting and why?",
  "answer": "In meeting TS3008d, Team TS3008 chose dark grey because user research showed consumers disliked bright remotes.",
  "is_sufficient": true,
  "insufficient_reason": null,
  "citations": [
    {
      "meeting_id": "TS3008d",
      "quote": "In the final meeting they chose dark grey because consumers found bright colours unattractive.",
      "speaker_label": "Speaker D",
      "speaker_role": "Marketing",
      "turn_id": "8f3b2e1d-4c5a-6b7c-8d9e-0f1a2b3c4d5e",
      "turn_index": 48
    }
  ],
  "steps_taken": [
    "input_validation",
    "query_analysis",
    "retrieval_planning",
    "tool_execution",
    "evidence_assessment",
    "answer_generation",
    "response_validation",
    "final_response"
  ],
  "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "iteration_count": 1,
  "team_code": "TS3008"
}
```

### 3.2 Session-Aware Query Resumption
**Endpoint**: `POST /api/v1/agent/sessions/{session_id}/query`

Resumes thread state using `session_id`, appending the new interaction to the persistent session history in PostgreSQL `agent_sessions`.

### 3.3 Session History Retrieval
**Endpoint**: `GET /api/v1/agent/sessions/{session_id}`

Returns complete chronological interaction history, turn counts, and question-answer records for auditability.

### 3.4 Agent Health & Configuration Inspection
**Endpoint**: `GET /api/v1/agent/status`

Inspects registered tools, active LLM provider, model name, checkpointer engine, and LangSmith tracing status:
```json
{
  "status": "operational",
  "model_provider": "OllamaLLMClient",
  "model_name": "llama3.2",
  "tools_available": [
    "hybrid_search",
    "search_temporal_memory",
    "get_meeting_details",
    "get_related_meetings",
    "get_memory_history"
  ],
  "checkpointer": "InMemorySaver",
  "langsmith_tracing": false
}
```

---

## 4. Model Configuration & Provider Swapping

Model providers are fully decoupled from graph execution logic via the `BaseLLMClient` interface (`app.services.llm_client`):

1. **Local Ollama (Default, Free & Offline)**:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   LLM_MODEL=llama3.2
   ```
2. **Deterministic Mock (Testing & Air-Gapped Environments)**:
   ```bash
   LLM_PROVIDER=mock
   ```
3. **Optional Cloud Provider (Gemini API)**:
   ```bash
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_key_here
   ```

No paid API key is ever mandatory to operate the system.

---

## 5. Troubleshooting & Failure Recovery

### Problem 1: Insufficient Evidence Halting
- **Symptom**: `is_sufficient` returns `false` with reason: `Insufficient cross-meeting evidence`.
- **Cause**: The question requires temporal progression across multiple meetings, but only one meeting was ingested or retrieved.
- **Resolution**:
  1. Verify all team meetings are ingested: `catalist ingest --dataset-path data/raw`.
  2. Increase iteration budget: pass `--max-iterations 3`.

### Problem 2: LLM Connection Failure (Ollama Offline)
- **Symptom**: Log warning `Ollama text generation failed... Using deterministic evidence fallback`.
- **Cause**: Ollama service is not running on `localhost:11434`.
- **Resolution**: The system automatically executes deterministic evidence synthesis without crashing. To restore LLM generation, start Ollama: `ollama run llama3.2`.

