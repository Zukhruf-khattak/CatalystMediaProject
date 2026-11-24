"""AgentService facade orchestrating LangGraph execution, session persistence, and API integration."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.graph import build_agent_graph
from app.agent.nodes import AgentNodes
from app.agent.state import AgentState
from app.agent.tools import AgentTools
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.agent import AgentSession
from app.schemas.agent import (
    AgentCitationItem,
    AgentQueryRequest,
    AgentQueryResponse,
    AgentSessionDetailResponse,
    AgentStatusResponse,
)
from app.schemas.retrieval import MemoryEvidenceItem, TranscriptEvidenceItem
from app.services.llm_client import BaseLLMClient, get_llm_client

logger = get_logger("app.agent.service")


class AgentService:
    """
    High-level service interface for the Catalist Meeting Intelligence research agent.
    Manages graph compilation, state checkpointing, database session logging, and telemetry.
    """

    def __init__(
        self,
        db: Session,
        llm_client: Optional[BaseLLMClient] = None,
        checkpointer: Optional[Any] = None,
    ) -> None:
        self.db = db
        self.llm_client = llm_client or get_llm_client()
        self.checkpointer = checkpointer or MemorySaver()
        self.tools = AgentTools(db)
        self.nodes = AgentNodes(self.tools, self.llm_client)
        self.graph = build_agent_graph(self.nodes, checkpointer=self.checkpointer)
        self.settings = get_settings()

    def query(self, request: AgentQueryRequest) -> AgentQueryResponse:
        """
        Execute a question-answering workflow through the LangGraph multi-step agent.
        Persists conversation turn and state snapshot to the PostgreSQL agent_sessions table.
        """
        session_id = request.session_id or str(uuid.uuid4())
        initial_state: AgentState = {
            "question": request.question,
            "team_code": request.team_code,
            "session_id": session_id,
            "iteration": 0,
            "max_iterations": request.max_iterations,
            "steps_taken": [],
        }

        config = {"configurable": {"thread_id": session_id}}
        logger.info(
            f"Invoking agent graph for session '{session_id}' with question: '{request.question[:80]}...'"
        )

        try:
            result_state = self.graph.invoke(initial_state, config=config)
        except Exception as e:
            logger.error(f"LangGraph execution exception: {e}", exc_info=True)
            result_state = {
                "question": request.question,
                "answer": "An error occurred while executing the agent workflow.",
                "is_sufficient": False,
                "insufficient_reason": f"Execution error: {str(e)}",
                "citations": [],
                "retrieved_turns": [],
                "retrieved_memories": [],
                "steps_taken": ["error_handler"],
                "iteration": 1,
            }

        answer = result_state.get("answer") or "No answer could be formed from available evidence."
        is_sufficient = bool(result_state.get("is_sufficient", False))
        insufficient_reason = result_state.get("insufficient_reason")
        iteration_count = result_state.get("iteration") or 1
        steps_taken = result_state.get("steps_taken") or []

        # Convert citations
        citations = []
        for c in result_state.get("citations") or []:
            try:
                citations.append(
                    AgentCitationItem(
                        meeting_id=c.get("meeting_id") or "Unknown",
                        quote=c.get("quote") or "",
                        speaker_label=c.get("speaker_label"),
                        speaker_role=c.get("speaker_role"),
                        turn_id=str(c.get("turn_id")) if c.get("turn_id") else None,
                        turn_index=c.get("turn_index"),
                    )
                )
            except Exception as e:
                logger.warning(f"Error parsing citation item {c}: {e}")

        # Convert supporting turns
        supporting_turns = []
        for t in (result_state.get("retrieved_turns") or [])[:10]:
            try:
                m_id_val = uuid.uuid4()
                if "meeting_id" in t:
                    try:
                        m_id_val = uuid.UUID(str(t["meeting_id"]))
                    except ValueError:
                        pass

                supporting_turns.append(
                    TranscriptEvidenceItem(
                        turn_id=uuid.UUID(str(t["turn_id"])) if "turn_id" in t else uuid.uuid4(),
                        meeting_id=m_id_val,
                        meeting_code=str(t.get("meeting_id") or "Unknown"),
                        turn_index=t.get("turn_index") or 0,
                        speaker_label=t.get("speaker_label") or "Unknown",
                        speaker_role=t.get("speaker_role"),
                        start_time_str=t.get("start_time") or "00:00:00",
                        raw_text=t.get("text") or "",
                        score=float(t.get("score") or 0.0),
                        retrieval_method=t.get("channel") or "agent_tool",
                    )
                )
            except Exception as e:
                logger.debug(f"Turn conversion notice: {e}")

        # Convert supporting memories
        supporting_memories = []
        for m in (result_state.get("retrieved_memories") or [])[:10]:
            try:
                m_code = str(m.get("meeting_id") or "Unknown")
                seq = m_code[-1] if m_code and m_code[-1].isalpha() else "a"
                supporting_memories.append(
                    MemoryEvidenceItem(
                        memory_id=uuid.UUID(str(m["memory_id"]))
                        if "memory_id" in m
                        else uuid.uuid4(),
                        team_code=str(request.team_code or "Unknown"),
                        meeting_code=m_code,
                        sequence_letter=seq,
                        meeting_order=int(m.get("meeting_order") or 1),
                        memory_type=m.get("memory_type") or "DECISION",
                        status=m.get("status") or "current",
                        statement=m.get("statement") or "",
                        quote=m.get("quote") or "",
                        speaker_label=m.get("speaker_label") or "Unknown",
                        confidence=float(m.get("score") or 1.0),
                    )
                )
            except Exception as e:
                logger.debug(f"Memory conversion notice: {e}")

        # Persist session state in database
        self._persist_session(
            session_id=session_id,
            team_code=request.team_code or result_state.get("team_code"),
            question=request.question,
            answer=answer,
            is_sufficient=is_sufficient,
            result_state=result_state,
        )

        return AgentQueryResponse(
            question=request.question,
            answer=answer,
            is_sufficient=is_sufficient,
            insufficient_reason=insufficient_reason,
            citations=citations,
            supporting_turns=supporting_turns,
            supporting_memories=supporting_memories,
            steps_taken=steps_taken,
            session_id=session_id,
            iteration_count=iteration_count,
            team_code=request.team_code or result_state.get("team_code"),
        )

    def query_session(self, session_id: str, request: AgentQueryRequest) -> AgentQueryResponse:
        """
        Execute a session-aware query, resuming existing conversational thread state.
        """
        request.session_id = session_id
        return self.query(request)

    def get_session(self, session_id: str) -> Optional[AgentSessionDetailResponse]:
        """
        Retrieve persisted session details and message history from the database.
        """
        stmt = select(AgentSession).where(AgentSession.session_id == session_id)
        session_row = self.db.execute(stmt).scalar_one_or_none()
        if not session_row:
            return None

        return AgentSessionDetailResponse(
            session_id=session_row.session_id,
            team_code=session_row.team_code,
            title=session_row.title,
            turn_count=session_row.turn_count,
            history=session_row.messages_json,
            created_at=session_row.created_at,
            updated_at=session_row.updated_at,
        )

    def get_status(self) -> AgentStatusResponse:
        """
        Return agent operational status, LLM configuration, available tools, and checkpoint engine.
        """
        tools_list = [
            "hybrid_search",
            "search_temporal_memory",
            "get_meeting_details",
            "get_related_meetings",
            "get_memory_history",
        ]
        provider_name = self.llm_client.__class__.__name__
        model_name = getattr(self.llm_client, "model", self.settings.llm_model)

        return AgentStatusResponse(
            status="operational",
            model_provider=provider_name,
            model_name=model_name,
            tools_available=tools_list,
            checkpointer=self.checkpointer.__class__.__name__,
            langsmith_tracing=self.settings.langsmith_tracing,
        )

    def _persist_session(
        self,
        session_id: str,
        team_code: Optional[str],
        question: str,
        answer: str,
        is_sufficient: bool,
        result_state: Dict[str, Any],
    ) -> None:
        """Helper to create or update AgentSession in the database."""
        try:
            stmt = select(AgentSession).where(AgentSession.session_id == session_id)
            session_row = self.db.execute(stmt).scalar_one_or_none()

            new_turn = {
                "question": question,
                "answer": answer,
                "is_sufficient": is_sufficient,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Lightweight snapshot omitting bulky raw embeddings
            safe_snapshot = {
                "iteration": result_state.get("iteration"),
                "is_sufficient": result_state.get("is_sufficient"),
                "team_code": team_code,
                "steps_taken": result_state.get("steps_taken"),
            }

            if not session_row:
                session_row = AgentSession(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    team_code=team_code,
                    title=question[:100],
                    turn_count=1,
                    messages_json=[new_turn],
                    state_snapshot=safe_snapshot,
                )
                self.db.add(session_row)
            else:
                updated_messages = list(session_row.messages_json or [])
                updated_messages.append(new_turn)
                session_row.messages_json = updated_messages
                session_row.state_snapshot = safe_snapshot
                session_row.turn_count = len(updated_messages)
                if team_code and not session_row.team_code:
                    session_row.team_code = team_code

            self.db.commit()
        except Exception as e:
            logger.error(f"Error persisting agent session '{session_id}': {e}")
            self.db.rollback()
