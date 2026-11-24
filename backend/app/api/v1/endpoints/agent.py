"""FastAPI endpoints exposing the LangGraph multi-step meeting intelligence agent."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agent.service import AgentService
from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentSessionDetailResponse,
    AgentStatusResponse,
)

logger = get_logger("app.api.v1.agent")
router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
    "/query",
    response_model=AgentQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute LangGraph cross-meeting research agent query",
    description=(
        "Executes a multi-step research workflow across transcript turns and temporal memories. "
        "Returns synthesized answer, exact citations, and supporting evidence."
    ),
)
def run_agent_query(
    request: AgentQueryRequest,
    db: Session = Depends(get_db),
) -> AgentQueryResponse:
    """Submit a question to the LangGraph meeting research agent."""
    service = AgentService(db=db)
    return service.query(request)


@router.post(
    "/sessions/{session_id}/query",
    response_model=AgentQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit question within an existing conversational session",
    description="Resumes agent session state using thread checkpointer and database history.",
)
@router.post(
    "/session/{session_id}/query",
    response_model=AgentQueryResponse,
    include_in_schema=False,
)
def run_session_query(
    session_id: str,
    request: AgentQueryRequest,
    db: Session = Depends(get_db),
) -> AgentQueryResponse:
    """Submit a question within a specific persistent conversation session."""
    service = AgentService(db=db)
    return service.query_session(session_id=session_id, request=request)


@router.get(
    "/sessions/{session_id}",
    response_model=AgentSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve session interaction history",
    description="Returns all questions, answers, and turn history recorded for the specified session.",
)
@router.get(
    "/session/{session_id}",
    response_model=AgentSessionDetailResponse,
    include_in_schema=False,
)
def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
) -> AgentSessionDetailResponse:
    """Retrieve history for an agent session."""
    service = AgentService(db=db)
    session_detail = service.get_session(session_id=session_id)
    if not session_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent session '{session_id}' not found.",
        )
    return session_detail


@router.get(
    "/status",
    response_model=AgentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent operational status and model configuration",
    description="Returns current status, active LLM provider, registered tools, and checkpointer engine.",
)
def get_agent_status(
    db: Session = Depends(get_db),
) -> AgentStatusResponse:
    """Inspect agent operational health and component configuration."""
    service = AgentService(db=db)
    return service.get_status()
