"""LangGraph StateGraph assembly for the Catalist Meeting Intelligence research agent."""

from typing import Any, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agent.nodes import AgentNodes
from app.agent.state import AgentState
from app.core.logging import get_logger

logger = get_logger("app.agent.graph")


def route_after_input_validation(state: AgentState) -> str:
    """Route to query analysis if input is valid, or shortcut to final response on error."""
    if state.get("error"):
        return "final_response"
    return "query_analysis"


def route_after_evidence_assessment(state: AgentState) -> str:
    """
    Route to answer generation if evidence is sufficient.
    Loop back to retrieval planning if missing facets can be retrieved within iteration budget.
    Shortcut to final response if evidence is insufficient and iterations exhausted.
    """
    if state.get("is_sufficient"):
        return "answer_generation"

    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 2)
    missing = state.get("missing_facets") or []

    if missing and iteration < max_iterations:
        logger.info(
            f"Evidence assessment flagged missing facets {missing} at iteration {iteration}/{max_iterations}. "
            "Routing back to retrieval planning."
        )
        return "retrieval_planning"

    logger.info(f"Insufficient evidence after {iteration} iterations. Routing to final response.")
    return "final_response"


def route_after_citation_validation(state: AgentState) -> str:
    """
    Route to final response if validation passed, or if retry budget is exhausted.
    Loop back to answer generation if validation failed and retries remain.
    """
    if state.get("validation_status") == "PASSED" or not state.get("is_sufficient"):
        return "final_response"

    retries = state.get("validation_retries", 0)
    max_retries = state.get("max_validation_retries", 2)

    if retries < max_retries:
        logger.info(
            f"Citation validation failed (retry {retries}/{max_retries}). "
            "Routing back to answer_generation."
        )
        return "answer_generation"

    logger.warning(
        f"Citation validation retry budget exhausted ({retries}/{max_retries}). "
        "Routing to final_response."
    )
    return "final_response"


def build_agent_graph(
    nodes: AgentNodes,
    checkpointer: Optional[Any] = None,
) -> CompiledStateGraph:
    """
    Assemble and compile the LangGraph workflow with deterministic citation validation.

    Workflow Structure:
        START -> input_validation
        input_validation -> query_analysis (valid) | final_response (invalid)
        query_analysis -> retrieval_planning
        retrieval_planning -> tool_execution
        tool_execution -> evidence_assessment
        evidence_assessment -> answer_generation (sufficient)
                            -> retrieval_planning (insufficient + budget remaining)
                            -> final_response (insufficient + budget exhausted)
        answer_generation -> citation_validation
        citation_validation -> final_response (passed or retries exhausted)
                            -> answer_generation (failed + retry budget remaining)
        final_response -> END
    """
    builder = StateGraph(AgentState)

    # Register all workflow nodes
    builder.add_node("input_validation", nodes.input_validation)
    builder.add_node("query_analysis", nodes.query_analysis)
    builder.add_node("retrieval_planning", nodes.retrieval_planning)
    builder.add_node("tool_execution", nodes.tool_execution)
    builder.add_node("evidence_assessment", nodes.evidence_assessment)
    builder.add_node("answer_generation", nodes.answer_generation)
    builder.add_node("citation_validation", nodes.citation_validation)
    builder.add_node("final_response", nodes.final_response)

    # Edges & Conditional Routing
    builder.add_edge(START, "input_validation")
    builder.add_conditional_edges(
        "input_validation",
        route_after_input_validation,
        {
            "query_analysis": "query_analysis",
            "final_response": "final_response",
        },
    )
    builder.add_edge("query_analysis", "retrieval_planning")
    builder.add_edge("retrieval_planning", "tool_execution")
    builder.add_edge("tool_execution", "evidence_assessment")
    builder.add_conditional_edges(
        "evidence_assessment",
        route_after_evidence_assessment,
        {
            "answer_generation": "answer_generation",
            "retrieval_planning": "retrieval_planning",
            "final_response": "final_response",
        },
    )
    builder.add_edge("answer_generation", "citation_validation")
    builder.add_conditional_edges(
        "citation_validation",
        route_after_citation_validation,
        {
            "final_response": "final_response",
            "answer_generation": "answer_generation",
        },
    )
    builder.add_edge("final_response", END)

    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()
