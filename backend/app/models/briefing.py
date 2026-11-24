"""Database model for persisted Team Pre-Meeting Briefings."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Briefing(Base):
    """
    Persisted Pre-Meeting Briefing for a specific team.
    Stores full Markdown report, structured JSON payload, citation validation status,
    covered meetings, and versioning metadata.
    """

    __tablename__ = "briefings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    target_meeting_code: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    structured_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), default="PASSED", nullable=False)
    validation_errors: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    citations_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meetings_covered: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    generation_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
