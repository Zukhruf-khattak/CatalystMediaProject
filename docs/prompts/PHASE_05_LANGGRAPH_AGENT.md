# Phase 5: LangGraph Agent Implementation

Act as a senior AI engineer.

Implement **Phase 5: LangGraph Agent** in the existing Catalist Meeting Intelligence project.

First inspect the repository and completed Phase 1–4 implementations, including database models, temporal memory, retrieval services, API contracts, and architecture documentation. Extend the existing components instead of duplicating them.

## Objective

Build a LangGraph-powered agent that answers questions about meeting history using tools, persistent memory, and retrieved evidence.

The agent must answer the 25 questions in `questions.json` and support the TS3012 briefing in a later phase.

## 1. LangGraph Workflow

Implement a graph with these nodes:

1. **Input Validation:** Validate the question and request context.
2. **Query Analysis:** Identify relevant teams, entities, time references, and information needs.
3. **Retrieval Planning:** Decide which retrieval tools are required.
4. **Tool Execution:** Retrieve transcript evidence and temporal memories.
5. **Evidence Assessment:** Check whether the retrieved evidence is sufficient.
6. **Answer Generation:** Generate a concise answer grounded in retrieved evidence.
7. **Response Validation:** Validate output structure and evidence references.
8. **Final Response:** Return the answer with supporting evidence or an explicit insufficient-evidence response.

Use conditional edges where the agent needs additional retrieval or must stop due to insufficient evidence.

## 2. Agent Tools

Expose existing services as LangGraph tools:

- `hybrid_search`: Search transcript chunks using Phase 4.
- `search_temporal_memory`: Retrieve decisions, actions, and unresolved issues.
- `get_meeting_details`: Retrieve meeting metadata and relevant segments.
- `get_related_meetings`: Find related meetings within a team.
- `get_memory_history`: Retrieve historical and superseded memories.

Tools must use existing database and service layers. Keep database access out of graph nodes where practical.

## 3. Agent Reasoning

The agent must:

- Handle questions requiring multiple meetings.
- Retrieve additional evidence when initial results are insufficient.
- Compare earlier and later statements.
- Distinguish current decisions from superseded decisions.
- Identify unresolved disagreements.
- Avoid unsupported conclusions.
- Return insufficient evidence when the corpus does not support an answer.

Use deterministic code for database operations, filtering, and validation. Use the LLM for query interpretation, retrieval planning where needed, and evidence-grounded answer generation.

## 4. Model Configuration

Use the existing model-provider abstraction.

Support a free/local model option and make model configuration environment-based. No paid API key should be mandatory.

Keep model selection separate from graph logic so providers can be changed without rewriting the workflow.

## 5. Persistence and Observability

- Persist conversation/session state using the existing PostgreSQL infrastructure.
- Support resuming a session where appropriate.
- Add LangSmith tracing when configured.
- Keep the application functional when LangSmith is unavailable.
- Trace graph nodes, tool names, execution times, and error categories.
- Do not send transcript text, quotations, or sensitive meeting content to tracing metadata.

## 6. API Integration

Expose the agent through FastAPI.

Provide:
- A question-answer endpoint.
- A session-aware endpoint.
- A health/status endpoint for agent and model configuration.

Use Pydantic request and response schemas. Follow the existing API conventions and return structured errors.

## 7. Testing

Add tests for:

- Graph execution and node transitions.
- Tool invocation.
- Multi-meeting questions.
- Temporal decision reasoning.
- Insufficient evidence.
- Tool failures and retries.
- Session persistence.
- Invalid model responses.
- Team isolation.
- API integration.

Use mocked LLM responses for deterministic tests. Include at least five representative end-to-end questions from the provided dataset.

## 8. Documentation

Update:

- `docs/02_SYSTEM_ARCHITECTURE.md`
- `docs/04_RETRIEVAL_AND_AGENT_DESIGN.md`
- `docs/06_API_CONTRACT.md`
- `docs/07_TESTING_AND_EVALUATION_PLAN.md`
- `docs/08_SECURITY_AND_PRIVACY.md`
- `docs/09_DEPLOYMENT_AND_OPERATIONS.md`
- `docs/10_PHASE_TRACKER.md`

Add:

- `docs/architecture/LANGGRAPH_WORKFLOW.md`
- `docs/operations/AGENT_RUNBOOK.md`

Save this prompt in:

`docs/prompts/PHASE_05_LANGGRAPH_AGENT.md`

Update `docs/prompts/README.md`.

## Acceptance Criteria

- LangGraph workflow executes successfully.
- Agent uses the existing retrieval and memory tools.
- Multi-meeting questions are supported.
- Temporal changes are handled using retrieved evidence.
- Unsupported answers return an insufficient-evidence response.
- Session persistence works.
- LangSmith is optional and does not affect core functionality.
- API endpoints work.
- Tests pass.
- Existing Phase 1–4 functionality remains operational.
- Documentation reflects the actual implementation.

Do not implement the dedicated citation-validation phase, TS3012 briefing, or React frontend. These belong to later phases.

At completion, report the graph structure, implemented tools, API endpoints, test results, execution commands, and known limitations.

**Stop after Phase 5 and wait for review.**
