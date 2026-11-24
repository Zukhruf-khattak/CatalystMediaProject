"""LangGraph agent tools wrapping Phase 1-4 retrieval, temporal memory, and database services."""

import time
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.dataset import Meeting, Team, TranscriptTurn
from app.schemas.memory import MemorySearchFilter
from app.schemas.retrieval import RetrievalRequest
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.services.memory_retrieval_service import MemoryRetrievalService

logger = get_logger("app.agent.tools")


class AgentTools:
    """
    Exposes meeting intelligence database and service layers as callable agent tools.
    Every tool returns plain Python dicts/lists to maintain clean separation between
    database access and LangGraph node orchestration.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.hybrid_service = HybridRetrievalService(db)
        self.memory_service = MemoryRetrievalService(db)

    def hybrid_search(
        self,
        query: str,
        team_code: Optional[str] = None,
        meeting_codes: Optional[List[str]] = None,
        limit: int = 10,
        method: str = "hybrid",
    ) -> Dict[str, Any]:
        """
        Search transcript chunks and temporal memories using Phase 4 hybrid retrieval.
        Combines lexical FTS and dense semantic search via Reciprocal Rank Fusion (RRF).
        """
        meeting_code = meeting_codes[0] if meeting_codes else None
        request = RetrievalRequest(
            query=query,
            team_code=team_code,
            meeting_code=meeting_code,
            method=method.lower() if method else "hybrid",
            limit=limit,
            include_temporal_memories=True,
        )
        pack = self.hybrid_service.execute_retrieval(request)

        turn_dicts = []
        for t in pack.transcript_segments:
            turn_dicts.append(
                {
                    "turn_id": str(t.turn_id),
                    "meeting_id": t.meeting_code,
                    "team_id": team_code,
                    "turn_index": t.turn_index,
                    "speaker_label": t.speaker_label,
                    "speaker_role": t.speaker_role,
                    "start_time": t.start_time_str,
                    "text": t.raw_text,
                    "score": t.score,
                    "channel": t.retrieval_method,
                }
            )

        mem_dicts = []
        for m in pack.temporal_memories + pack.unresolved_disagreements:
            mem_dicts.append(
                {
                    "memory_id": str(m.memory_id),
                    "memory_type": m.memory_type,
                    "statement": m.statement,
                    "quote": m.quote,
                    "status": m.status,
                    "meeting_id": m.meeting_code,
                    "meeting_order": m.meeting_order,
                    "speaker_label": m.speaker_label,
                    "speaker_role": m.speaker_role,
                    "turn_id": str(m.turn_id) if m.turn_id else None,
                    "score": m.confidence,
                    "channel": "temporal_memory",
                    "linked_memory_ids": [
                        str(r.target_memory_id) for r in m.outgoing_relationships
                    ],
                }
            )

        return {
            "query": pack.query,
            "turns": turn_dicts,
            "memories": mem_dicts,
            "total_turn_candidates": len(turn_dicts),
            "total_memory_candidates": len(mem_dicts),
        }

    def search_temporal_memory(
        self,
        query: str,
        team_code: Optional[str] = None,
        memory_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve decisions, actions, disagreements, and commitments from the temporal memory store.
        """
        filters = MemorySearchFilter(
            team_code=team_code,
            query_text=query,
            memory_type=memory_type.upper() if memory_type else None,
            status=status.lower() if status else None,
            page=1,
            page_size=limit,
        )
        memories, _ = self.memory_service.search_memories(filters)
        return [
            {
                "memory_id": str(m.id),
                "memory_type": m.memory_type,
                "statement": m.statement,
                "quote": m.quote,
                "status": m.status,
                "meeting_id": m.meeting.meeting_code if m.meeting else None,
                "meeting_order": m.meeting_order,
                "speaker_label": m.speaker_label,
                "speaker_role": m.speaker_role,
                "turn_id": str(m.turn_id) if m.turn_id else None,
            }
            for m in memories
        ]

    def get_meeting_details(self, meeting_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve meeting metadata, team association, and speaker roster for a specific meeting.
        """
        stmt = (
            select(Meeting)
            .where(Meeting.meeting_code == meeting_code)
            .options(
                selectinload(Meeting.team),
                selectinload(Meeting.speakers),
            )
        )
        meeting = self.db.execute(stmt).scalar_one_or_none()
        if not meeting:
            return None

        turn_count_stmt = select(func.count(TranscriptTurn.id)).where(
            TranscriptTurn.meeting_id == meeting.id
        )
        turn_count = self.db.execute(turn_count_stmt).scalar() or 0

        return {
            "meeting_code": meeting.meeting_code,
            "team_code": meeting.team.team_code if meeting.team else None,
            "sequence_letter": meeting.sequence_letter,
            "meeting_order": meeting.meeting_number,
            "total_turns": turn_count,
            "speakers": [
                {
                    "speaker_label": s.speaker_label,
                    "speaker_role": s.role,
                }
                for s in meeting.speakers
            ],
        }

    def get_related_meetings(self, team_code: str) -> List[Dict[str, Any]]:
        """
        Find all meetings belonging to a team in chronological order.
        """
        stmt = (
            select(Meeting)
            .join(Team, Meeting.team_id == Team.id)
            .where(Team.team_code == team_code)
            .order_by(Meeting.meeting_number.asc())
        )
        meetings = self.db.execute(stmt).scalars().all()
        results = []
        for m in meetings:
            turn_count_stmt = select(func.count(TranscriptTurn.id)).where(
                TranscriptTurn.meeting_id == m.id
            )
            turn_count = self.db.execute(turn_count_stmt).scalar() or 0
            results.append(
                {
                    "meeting_code": m.meeting_code,
                    "sequence_letter": m.sequence_letter,
                    "meeting_order": m.meeting_number,
                    "turn_count": turn_count,
                }
            )
        return results

    def get_memory_history(self, memory_id: str) -> Dict[str, Any]:
        """
        Retrieve complete chronological evolution and relationship graph for a specific memory.
        Traverses supersedes, updates, resolves, supports, and contradicts edges.
        """
        try:
            m_uuid = uuid.UUID(memory_id)
        except ValueError:
            return {"error": f"Invalid UUID: {memory_id}", "history": []}

        memory = self.memory_service.get_memory_by_id(m_uuid)
        if not memory:
            return {"error": f"Memory {memory_id} not found", "history": []}

        chain = [
            {
                "memory_id": str(memory.id),
                "meeting_id": memory.meeting.meeting_code if memory.meeting else None,
                "meeting_order": memory.meeting_order,
                "statement": memory.statement,
                "quote": memory.quote,
                "status": memory.status,
                "relation": "origin",
            }
        ]

        # Outgoing: target memories that this memory supersedes/updates
        for rel in memory.outgoing_relationships:
            target = rel.target_memory
            if target:
                chain.append(
                    {
                        "memory_id": str(target.id),
                        "meeting_id": target.meeting.meeting_code if target.meeting else None,
                        "meeting_order": target.meeting_order,
                        "statement": target.statement,
                        "quote": target.quote,
                        "status": target.status,
                        "relation": f"{rel.relationship_type}_target",
                    }
                )

        # Incoming: newer memories that supersede/update this memory
        for rel in memory.incoming_relationships:
            source = rel.source_memory
            if source:
                chain.append(
                    {
                        "memory_id": str(source.id),
                        "meeting_id": source.meeting.meeting_code if source.meeting else None,
                        "meeting_order": source.meeting_order,
                        "statement": source.statement,
                        "quote": source.quote,
                        "status": source.status,
                        "relation": f"source_that_{rel.relationship_type}",
                    }
                )

        # Sort chain chronologically by meeting_order
        chain.sort(key=lambda x: x.get("meeting_order") or 0)
        return {
            "root_memory_id": memory_id,
            "status": memory.status,
            "history": chain,
        }

    def execute_tool(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Safely execute a tool by name with telemetry tracking.
        """
        start_time = time.perf_counter()
        try:
            if tool_name == "hybrid_search":
                res = self.hybrid_search(**kwargs)
            elif tool_name == "search_temporal_memory":
                res = self.search_temporal_memory(**kwargs)
            elif tool_name == "get_meeting_details":
                res = self.get_meeting_details(**kwargs)
            elif tool_name == "get_related_meetings":
                res = self.get_related_meetings(**kwargs)
            elif tool_name == "get_memory_history":
                res = self.get_memory_history(**kwargs)
            else:
                return {
                    "tool": tool_name,
                    "error": f"Unknown tool: {tool_name}",
                    "duration_ms": 0.0,
                }

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "tool": tool_name,
                "result": res,
                "duration_ms": round(duration_ms, 2),
                "error": None,
            }
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Agent tool '{tool_name}' execution error: {e}")
            return {
                "tool": tool_name,
                "result": None,
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
            }
