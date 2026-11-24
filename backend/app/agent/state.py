"""Agent state definitions for LangGraph multi-step meeting intelligence reasoning."""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """
    State dictionary flowing through all nodes of the LangGraph meeting research agent.
    Maintains inputs, query analysis, retrieval plan, accumulated evidence,
    assessment flags, generated answers, citations, and execution telemetry.
    """

    # Input & Session Context
    question: str
    team_code: Optional[str]
    session_id: str
    iteration: int
    max_iterations: int

    # Stage 1: Query Analysis
    query_analysis: Dict[str, Any]

    # Stage 2: Retrieval Planning
    retrieval_plan: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]

    # Stage 3: Accumulated Evidence
    retrieved_turns: List[Dict[str, Any]]
    retrieved_memories: List[Dict[str, Any]]
    meeting_contexts: List[Dict[str, Any]]
    memory_histories: List[Dict[str, Any]]

    # Stage 4: Evidence Assessment
    is_sufficient: bool
    insufficient_reason: Optional[str]
    missing_facets: List[str]

    # Stage 5 & 6: Answer Generation & Validation
    answer: Optional[str]
    citations: List[Dict[str, Any]]
    validation_errors: List[str]

    # Observability & Traceability
    steps_taken: List[str]
    error: Optional[str]
