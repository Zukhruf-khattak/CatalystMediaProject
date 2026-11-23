import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.dataset import Meeting, Team
from app.models.memory import Memory
from app.schemas.memory import MemorySearchFilter

logger = get_logger("app.services.memory_retrieval")


class MemoryRetrievalService:
    """Service providing query, filter, and pagination capabilities over stored temporal memories."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_memory_by_id(self, memory_id: uuid.UUID) -> Optional[Memory]:
        """Retrieve a single memory record by ID with relationships eagerly loaded."""
        stmt = (
            select(Memory)
            .where(Memory.id == memory_id)
            .options(
                selectinload(Memory.outgoing_relationships),
                selectinload(Memory.incoming_relationships),
                selectinload(Memory.meeting),
                selectinload(Memory.team),
                selectinload(Memory.turn),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search_memories(
        self,
        filters: MemorySearchFilter,
    ) -> Tuple[List[Memory], int]:
        """Search and filter memories across teams, meetings, types, and lifecycle statuses."""
        query = (
            select(Memory)
            .join(Meeting, Memory.meeting_id == Meeting.id)
            .join(Team, Memory.team_id == Team.id)
        )
        count_query = (
            select(func.count(Memory.id))
            .join(Meeting, Memory.meeting_id == Meeting.id)
            .join(Team, Memory.team_id == Team.id)
        )

        conditions = []

        # Team filtering
        if filters.team_id:
            conditions.append(Memory.team_id == filters.team_id)
        elif filters.team_code:
            conditions.append(Team.team_code == filters.team_code)

        # Meeting filtering
        if filters.meeting_code:
            conditions.append(Meeting.meeting_code == filters.meeting_code)
        if filters.meeting_order is not None:
            conditions.append(Memory.meeting_order == filters.meeting_order)
        if filters.sequence_letter:
            conditions.append(Memory.sequence_letter == filters.sequence_letter.lower())

        # Type & Status filtering
        if filters.memory_type:
            conditions.append(Memory.memory_type == filters.memory_type.upper())
        if filters.status:
            conditions.append(Memory.status == filters.status.lower())

        # Text query filtering
        if filters.query_text and filters.query_text.strip():
            term = f"%{filters.query_text.strip()}%"
            conditions.append(
                or_(
                    Memory.statement.ilike(term),
                    Memory.quote.ilike(term),
                )
            )

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        # Total count
        total_count = self.db.execute(count_query).scalar_one()

        # Eager load relationships and apply pagination
        query = (
            query.options(
                selectinload(Memory.outgoing_relationships),
                selectinload(Memory.incoming_relationships),
                selectinload(Memory.meeting),
                selectinload(Memory.team),
            )
            .order_by(Memory.meeting_order.asc(), Memory.created_at.asc())
            .limit(filters.limit)
            .offset(filters.offset)
        )

        items = self.db.execute(query).scalars().all()
        return list(items), total_count

    def get_team_timeline(self, team_code: str) -> List[Memory]:
        """Retrieve full chronological evolution of memories for a given team."""
        stmt = (
            select(Memory)
            .join(Team, Memory.team_id == Team.id)
            .where(Team.team_code == team_code)
            .options(
                selectinload(Memory.outgoing_relationships),
                selectinload(Memory.incoming_relationships),
            )
            .order_by(Memory.meeting_order.asc(), Memory.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
