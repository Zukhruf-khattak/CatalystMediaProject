import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.memory import (
    Memory,
    MemoryRelationship,
    MemoryStatus,
    MemoryType,
    RelationshipType,
)

logger = get_logger("app.services.temporal_reasoning")


class TemporalReasoningService:
    """Service to discover and link chronological relationships between team memories."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def link_memory_to_prior_memories(
        self,
        new_memory: Memory,
        candidate_rel: Optional[str] = None,
        target_memory_id: Optional[uuid.UUID] = None,
        rationale: Optional[str] = None,
        is_ambiguous: bool = False,
    ) -> List[MemoryRelationship]:
        """Establish temporal relationships between a new memory and earlier memories for the same team."""
        created_relationships: List[MemoryRelationship] = []

        # Target explicit relationship if target_memory_id is provided
        if target_memory_id:
            target = self.db.get(Memory, target_memory_id)
            if target and target.team_id == new_memory.team_id:
                rel = self._create_relationship(
                    source=new_memory,
                    target=target,
                    rel_type=candidate_rel or RelationshipType.UPDATES.value,
                    rationale=rationale,
                    is_ambiguous=is_ambiguous,
                )
                if rel:
                    created_relationships.append(rel)
            return created_relationships

        # Otherwise, discover earlier memories for the same team on matching topics/types
        topic = new_memory.metadata_json.get("topic")
        query = (
            select(Memory)
            .where(
                Memory.team_id == new_memory.team_id,
                Memory.id != new_memory.id,
                Memory.meeting_order <= new_memory.meeting_order,
            )
            .order_by(Memory.meeting_order.desc(), Memory.created_at.desc())
        )
        prior_memories = self.db.execute(query).scalars().all()

        for prior in prior_memories:
            # Check for topic match or matching semantic target
            prior_topic = prior.metadata_json.get("topic")
            has_matching_topic = bool(
                topic and prior_topic and topic.lower() == prior_topic.lower()
            )

            # Evaluate Decision Supersession
            if (
                new_memory.memory_type == MemoryType.DECISION.value
                and prior.memory_type == MemoryType.DECISION.value
            ):
                if has_matching_topic:
                    # Decide if this supersedes or supports
                    rel_type = candidate_rel or RelationshipType.SUPERSEDES.value
                    rel = self._create_relationship(
                        source=new_memory,
                        target=prior,
                        rel_type=rel_type,
                        rationale=rationale
                        or f"Decision in meeting {new_memory.sequence_letter} supersedes meeting {prior.sequence_letter} on topic '{topic}'.",
                        is_ambiguous=is_ambiguous,
                    )
                    if rel:
                        created_relationships.append(rel)
                        if not is_ambiguous and rel_type == RelationshipType.SUPERSEDES.value:
                            # Mark older decision as superseded; newer remains current
                            prior.status = MemoryStatus.SUPERSEDED.value
                            new_memory.status = MemoryStatus.CURRENT.value
                            self.db.flush()
                    break

            # Evaluate Action Resolution
            elif (
                new_memory.memory_type == MemoryType.ACTION.value
                and prior.memory_type == MemoryType.ACTION.value
            ):
                if has_matching_topic and candidate_rel == RelationshipType.RESOLVES.value:
                    rel = self._create_relationship(
                        source=new_memory,
                        target=prior,
                        rel_type=RelationshipType.RESOLVES.value,
                        rationale=rationale
                        or f"Action in meeting {new_memory.sequence_letter} resolves action from meeting {prior.sequence_letter}.",
                        is_ambiguous=is_ambiguous,
                    )
                    if rel:
                        created_relationships.append(rel)
                        if not is_ambiguous:
                            prior.status = MemoryStatus.RESOLVED.value
                            self.db.flush()
                    break

            # Evaluate Disagreement Resolution / Reopening
            elif prior.memory_type == MemoryType.DISAGREEMENT.value and has_matching_topic:
                if candidate_rel == RelationshipType.RESOLVES.value:
                    rel = self._create_relationship(
                        source=new_memory,
                        target=prior,
                        rel_type=RelationshipType.RESOLVES.value,
                        rationale=rationale
                        or "Disagreement resolved by consensus in later meeting.",
                        is_ambiguous=is_ambiguous,
                    )
                    if rel:
                        created_relationships.append(rel)
                        if not is_ambiguous:
                            prior.status = MemoryStatus.RESOLVED.value
                            self.db.flush()
                elif candidate_rel == RelationshipType.REOPENS.value:
                    rel = self._create_relationship(
                        source=new_memory,
                        target=prior,
                        rel_type=RelationshipType.REOPENS.value,
                        rationale=rationale or "Previous disagreement reopened in later meeting.",
                        is_ambiguous=is_ambiguous,
                    )
                    if rel:
                        created_relationships.append(rel)
                        prior.status = MemoryStatus.OPEN.value
                        self.db.flush()

        return created_relationships

    def _create_relationship(
        self,
        source: Memory,
        target: Memory,
        rel_type: str,
        rationale: Optional[str] = None,
        is_ambiguous: bool = False,
    ) -> Optional[MemoryRelationship]:
        """Insert or ignore a memory relationship without duplication."""
        # Check if identical relationship already exists
        existing = self.db.execute(
            select(MemoryRelationship).where(
                MemoryRelationship.source_memory_id == source.id,
                MemoryRelationship.target_memory_id == target.id,
                MemoryRelationship.relationship_type == rel_type,
            )
        ).scalar_one_or_none()

        if existing:
            return None

        rel = MemoryRelationship(
            id=uuid.uuid4(),
            source_memory_id=source.id,
            target_memory_id=target.id,
            relationship_type=rel_type,
            rationale=rationale,
            is_ambiguous=is_ambiguous,
            confidence=1.0 if not is_ambiguous else 0.5,
        )
        self.db.add(rel)
        self.db.flush()
        logger.info(
            f"Created relationship: Memory[{str(source.id)[:8]}] -({rel_type})-> Memory[{str(target.id)[:8]}] "
            f"[ambiguous={is_ambiguous}]"
        )
        return rel
