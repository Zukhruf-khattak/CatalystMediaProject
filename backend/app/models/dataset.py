import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CrossDialectVector(TypeDecorator):
    """Vector type that maps to native pgvector Vector on PostgreSQL and Text on SQLite."""

    impl = Vector
    cache_ok = True

    def __init__(self, dim: int = 384, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(Text())


class CrossDialectTSVector(TypeDecorator):
    """TSVector type that maps to native PostgreSQL TSVECTOR and Text on SQLite."""

    impl = TSVECTOR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(TSVECTOR())
        return dialect.type_descriptor(Text())


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Team(Base):
    """Design team participating in meeting series."""

    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    team_code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        doc="Team identifier, e.g. ES2002, TS3012",
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
    meetings: Mapped[List["Meeting"]] = relationship(
        "Meeting",
        back_populates="team",
        cascade="all, delete-orphan",
        order_by="Meeting.sequence_letter",
    )


class Meeting(Base):
    """Individual meeting within a team's series."""

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meeting_code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique meeting identifier, e.g. ES2002a",
    )
    meeting_number: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        doc="Numeric meeting sequence in team series (1-4)",
    )
    sequence_letter: Mapped[Optional[str]] = mapped_column(
        String(4),
        nullable=True,
        doc="Letter sequence in team series (a, b, c, d)",
    )
    total_turns: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Count of individual speaker turns",
    )
    word_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total word count of all speaker utterances",
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Approximate meeting duration in seconds from last turn",
    )
    source_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Filename of source transcript, e.g. ES2002a.txt",
    )
    source_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="SHA-256 hash of original transcript file content",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="INGESTED",
        nullable=False,
        doc="Ingestion status: INGESTED, FAILED, PENDING",
    )
    raw_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Immutable verbatim original transcript text",
    )
    parser_version: Mapped[str] = mapped_column(
        String(32),
        default="1.0.0",
        nullable=False,
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
    team: Mapped["Team"] = relationship("Team", back_populates="meetings")
    speakers: Mapped[List["Speaker"]] = relationship(
        "Speaker",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="Speaker.speaker_label",
    )
    turns: Mapped[List["TranscriptTurn"]] = relationship(
        "TranscriptTurn",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptTurn.turn_index",
    )


class Speaker(Base):
    """Meeting-scoped speaker record.

    Note: Speaker A in meeting ES2002a is strictly distinct from Speaker A in ES2002b
    or TS3001a; roles may differ across meetings.
    """

    __tablename__ = "speakers"
    __table_args__ = (
        UniqueConstraint("meeting_id", "speaker_label", name="uq_speaker_meeting_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    speaker_label: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Exact transcript speaker label, e.g. Speaker A",
    )
    speaker_letter: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        doc="Single-letter speaker designation, e.g. A, B, C, D",
    )
    role: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Explicit role if stated in transcript roster, e.g. Project Manager",
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
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="speakers")
    turns: Mapped[List["TranscriptTurn"]] = relationship(
        "TranscriptTurn",
        back_populates="speaker",
        cascade="all, delete-orphan",
    )


class TranscriptTurn(Base):
    """Atomic speaker turn utterance: canonical ground-truth evidence unit."""

    __tablename__ = "transcript_turns"
    __table_args__ = (
        UniqueConstraint("meeting_id", "turn_index", name="uq_turn_meeting_index"),
        Index("idx_turns_meeting_index", "meeting_id", "turn_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    speaker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("speakers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="0-based monotonic index of turn within this meeting",
    )
    start_time_str: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="Original timestamp string, e.g. 00:00:50",
    )
    start_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Parsed start time in total seconds from meeting start",
    )
    end_time_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Estimated or parsed end time in seconds",
    )
    raw_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Exact original speech text preserving disfluencies and fillers",
    )
    normalized_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Whitespace-normalized text for lexical indexing",
    )
    search_vector: Mapped[Optional[str]] = mapped_column(
        CrossDialectTSVector,
        nullable=True,
        doc="PostgreSQL tsvector column for full-text search",
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        CrossDialectVector(dim=384),
        nullable=True,
        doc="384-dimensional dense vector (sentence-transformers/all-MiniLM-L6-v2)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="turns")
    speaker: Mapped["Speaker"] = relationship("Speaker", back_populates="turns")


class IngestionJob(Base):
    """Audit log and progress tracker for batch dataset ingestion jobs."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
        doc="Status: PENDING, RUNNING, COMPLETED, FAILED, PARTIAL",
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
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_turns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_words: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedded_turns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    errors_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        doc="List of error records with filename and trace context",
    )
    summary_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        doc="Summary statistics and metadata",
    )
