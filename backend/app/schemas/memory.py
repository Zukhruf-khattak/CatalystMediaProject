import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MemoryRelationshipBase(BaseModel):
    """Base schema for memory-to-memory relationships."""

    relationship_type: str = Field(
        ...,
        description="supports, contradicts, updates, supersedes, resolves, reopens",
    )
    rationale: Optional[str] = Field(None, description="Explanation for the relationship")
    is_ambiguous: bool = Field(False, description="True if relationship is uncertain")
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class MemoryRelationshipCreate(MemoryRelationshipBase):
    """Payload to create a new relationship between two memories."""

    source_memory_id: uuid.UUID
    target_memory_id: uuid.UUID


class MemoryRelationshipResponse(MemoryRelationshipBase):
    """Response representation of a memory relationship."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_memory_id: uuid.UUID
    target_memory_id: uuid.UUID
    created_at: datetime


class MemoryBase(BaseModel):
    """Base schema for an atomic memory item."""

    memory_type: str = Field(
        ...,
        description="DECISION, ACTION, PREFERENCE, REQUIREMENT, DISAGREEMENT, ENTITY",
    )
    statement: str = Field(..., min_length=3, description="Clear atomic statement")
    quote: str = Field(..., min_length=5, description="Exact supporting quotation from transcript")
    speaker_label: str = Field(..., description="Speaker label, e.g. Speaker B")
    speaker_role: Optional[str] = Field(None, description="Speaker role if known")
    meeting_order: int = Field(..., ge=1, le=4, description="Meeting number in series (1-4)")
    sequence_letter: str = Field(..., description="Meeting sequence letter (a-d)")
    status: str = Field("current", description="current, superseded, open, resolved, rejected")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    extraction_version: str = Field("1.0.0")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class MemoryCreate(MemoryBase):
    """Payload to create a memory item."""

    team_id: uuid.UUID
    meeting_id: uuid.UUID
    turn_id: Optional[uuid.UUID] = None


class MemoryResponse(MemoryBase):
    """Complete response model for a memory record including relationships."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    meeting_id: uuid.UUID
    turn_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    outgoing_relationships: List[MemoryRelationshipResponse] = Field(default_factory=list)
    incoming_relationships: List[MemoryRelationshipResponse] = Field(default_factory=list)


class MemorySearchFilter(BaseModel):
    """Query parameters for searching and filtering temporal memory."""

    team_code: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    meeting_code: Optional[str] = None
    meeting_order: Optional[int] = Field(None, ge=1, le=4)
    sequence_letter: Optional[str] = None
    memory_type: Optional[str] = None
    status: Optional[str] = None
    query_text: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class MemorySearchResponse(BaseModel):
    """Paginated search response for memories."""

    items: List[MemoryResponse]
    total_count: int
    limit: int
    offset: int


class MemoryExtractionRequest(BaseModel):
    """Request options to extract temporal memories."""

    team_code: Optional[str] = Field(None, description="Target team code, e.g. TS3006")
    meeting_code: Optional[str] = Field(None, description="Target meeting code, e.g. TS3006a")
    force: bool = Field(
        False, description="Whether to re-extract memories for already processed meetings"
    )
    extraction_version: str = Field("1.0.0", description="Extraction engine version tag")


class MemoryExtractionRunResponse(BaseModel):
    """Response model for a memory extraction run."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: Optional[uuid.UUID] = None
    meeting_id: Optional[uuid.UUID] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_turns_analyzed: int
    total_memories_extracted: int
    total_memories_validated: int
    total_memories_rejected: int
    total_relationships_created: int
    errors_json: List[Dict[str, Any]] = Field(default_factory=list)
    summary_json: Dict[str, Any] = Field(default_factory=dict)
