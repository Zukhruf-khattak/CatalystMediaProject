import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.dataset import CrossDialectVector, utc_now


class MemoryType(str, Enum):
    """Semantic category of extracted temporal memory."""

    DECISION = "DECISION"
    ACTION = "ACTION"
    PREFERENCE = "PREFERENCE"
    REQUIREMENT = "REQUIREMENT"
    DISAGREEMENT = "DISAGREEMENT"
    ENTITY = "ENTITY"


class MemoryStatus(str, Enum):
    """Lifecycle status of a temporal memory record."""

    CURRENT = "current"
    SUPERSEDED = "superseded"
    OPEN = "open"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class RelationshipType(str, Enum):
    """Directed temporal and logical relationships between memory items."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    UPDATES = "updates"
    SUPERSEDES = "supersedes"
    RESOLVES = "resolves"
    REOPENS = "reopens"


class Memory(Base):
    """Atomic ground-truth memory record extracted from meeting transcript."""

    __tablename__ = "memories"
    __table_args__ = (
        Index("idx_memories_team_type_status", "team_id", "memory_type", "status"),
        Index("idx_memories_meeting_order", "meeting_id", "meeting_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("transcript_turns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Primary supporting transcript turn ID",
    )
    memory_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        doc="DECISION, ACTION, PREFERENCE, REQUIREMENT, DISAGREEMENT, ENTITY",
    )
    statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Clear, atomic statement of the fact, decision, or action",
    )
    quote: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Exact verbatim transcript quotation serving as ground-truth citation",
    )
    speaker_label: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Speaker label (e.g. Speaker A, Speaker B)",
    )
    speaker_role: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Speaker role if known (e.g. Project Manager, Industrial Designer)",
    )
    meeting_order: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        doc="Sequential order of meeting in team series (1-4)",
    )
    sequence_letter: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
        doc="Letter identifier of meeting (a, b, c, d)",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=MemoryStatus.CURRENT.value,
        nullable=False,
        index=True,
        doc="current, superseded, open, resolved, rejected",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        doc="Extraction confidence score (0.0 to 1.0)",
    )
    extraction_version: Mapped[str] = mapped_column(
        String(32),
        default="1.0.0",
        nullable=False,
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        CrossDialectVector(dim=384),
        nullable=True,
        doc="384-dimensional dense vector of the memory statement",
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        doc="Supplementary structured attributes (e.g. owner, deadline, cost)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    team = relationship("Team")
    meeting = relationship("Meeting")
    turn = relationship("TranscriptTurn")

    outgoing_relationships: Mapped[List["MemoryRelationship"]] = relationship(
        "MemoryRelationship",
        foreign_keys="[MemoryRelationship.source_memory_id]",
        back_populates="source_memory",
        cascade="all, delete-orphan",
    )
    incoming_relationships: Mapped[List["MemoryRelationship"]] = relationship(
        "MemoryRelationship",
        foreign_keys="[MemoryRelationship.target_memory_id]",
        back_populates="target_memory",
        cascade="all, delete-orphan",
    )


class MemoryRelationship(Base):
    """Directed temporal edge connecting a newer memory to an older memory."""

    __tablename__ = "memory_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_memory_id",
            "target_memory_id",
            "relationship_type",
            name="uq_memory_rel_source_target_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    source_memory_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The newer or asserting memory",
    )
    target_memory_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The earlier or target memory being modified/supported",
    )
    relationship_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        doc="supports, contradicts, updates, supersedes, resolves, reopens",
    )
    rationale: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Explanation of why this relationship was established",
    )
    is_ambiguous: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="True if the relationship is uncertain and should not automatically alter status",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    source_memory: Mapped["Memory"] = relationship(
        "Memory",
        foreign_keys=[source_memory_id],
        back_populates="outgoing_relationships",
    )
    target_memory: Mapped["Memory"] = relationship(
        "Memory",
        foreign_keys=[target_memory_id],
        back_populates="incoming_relationships",
    )


class MemoryExtractionRun(Base):
    """Audit log tracking execution of memory extraction runs."""

    __tablename__ = "memory_extraction_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("meetings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
        doc="PENDING, RUNNING, COMPLETED, FAILED, PARTIAL",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    total_turns_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_memories_extracted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_memories_validated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_memories_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_relationships_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    summary_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
