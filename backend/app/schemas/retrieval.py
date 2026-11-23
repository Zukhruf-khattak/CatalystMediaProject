import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.memory import MemoryRelationshipResponse


class RetrievalMethod(str, Enum):
    """Supported retrieval methods."""

    HYBRID = "hybrid"
    KEYWORD = "keyword"
    VECTOR = "vector"
    TEMPORAL = "temporal"


class RetrievalFilter(BaseModel):
    """Structured filters applied during retrieval."""

    team_code: Optional[str] = Field(None, description="Target team code, e.g. TS3006")
    meeting_code: Optional[str] = Field(None, description="Target meeting code, e.g. TS3006a")
    speaker_label: Optional[str] = Field(None, description="Speaker label, e.g. Speaker B")
    speaker_role: Optional[str] = Field(None, description="Speaker role, e.g. Project Manager")
    sequence_letters: Optional[List[str]] = Field(
        None, description="Filter to specific meeting letters ['a', 'c']"
    )
    memory_type: Optional[str] = Field(None, description="DECISION, ACTION, DISAGREEMENT, etc.")
    status: Optional[str] = Field(None, description="current, superseded, open, resolved")


class ProcessedQuery(BaseModel):
    """Query analysis result with extracted entities and search terms."""

    raw_query: str
    cleaned_keyword_query: str
    extracted_team: Optional[str] = None
    extracted_meetings: List[str] = Field(default_factory=list)
    extracted_speakers: List[str] = Field(default_factory=list)
    extracted_topics: List[str] = Field(default_factory=list)
    temporal_intent: Optional[str] = Field(
        None, description="initial, change, final, conflict, cost"
    )


class RetrievalRequest(BaseModel):
    """Payload for executing a retrieval query."""

    query: str = Field(..., min_length=2, description="Natural language question or query string")
    team_code: Optional[str] = Field(None, description="Optional explicit team filter")
    meeting_code: Optional[str] = Field(None, description="Optional explicit meeting filter")
    method: str = Field("hybrid", description="hybrid, keyword, vector, temporal")
    limit: int = Field(10, ge=1, le=100, description="Max transcript turns to return")
    rrf_k: int = Field(60, ge=1, le=200, description="Reciprocal Rank Fusion constant k")
    weight_keyword: float = Field(1.0, ge=0.0, description="Weight for keyword channel in RRF")
    weight_vector: float = Field(1.0, ge=0.0, description="Weight for vector channel in RRF")
    include_temporal_memories: bool = Field(
        True, description="Whether to include related temporal memories"
    )


class TranscriptEvidenceItem(BaseModel):
    """Retrieved transcript segment evidence unit."""

    model_config = ConfigDict(from_attributes=True)

    turn_id: uuid.UUID
    meeting_id: uuid.UUID
    meeting_code: str
    meeting_number: Optional[int] = None
    sequence_letter: Optional[str] = None
    turn_index: int
    speaker_label: str
    speaker_role: Optional[str] = None
    start_time_str: str
    raw_text: str
    score: float
    retrieval_method: str
    keyword_rank: Optional[int] = None
    vector_rank: Optional[int] = None


class MemoryEvidenceItem(BaseModel):
    """Retrieved atomic temporal memory evidence unit."""

    model_config = ConfigDict(from_attributes=True)

    memory_id: uuid.UUID
    team_code: str
    meeting_code: str
    sequence_letter: str
    meeting_order: int
    memory_type: str
    status: str
    statement: str
    quote: str
    speaker_label: str
    speaker_role: Optional[str] = None
    turn_id: Optional[uuid.UUID] = None
    confidence: float
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    outgoing_relationships: List[MemoryRelationshipResponse] = Field(default_factory=list)
    incoming_relationships: List[MemoryRelationshipResponse] = Field(default_factory=list)


class EvidencePackResponse(BaseModel):
    """Unified cross-meeting evidence pack returned to researchers and agents."""

    query: str
    processed_query: ProcessedQuery
    retrieval_method: str
    total_results: int
    transcript_segments: List[TranscriptEvidenceItem] = Field(default_factory=list)
    temporal_memories: List[MemoryEvidenceItem] = Field(default_factory=list)
    unresolved_disagreements: List[MemoryEvidenceItem] = Field(default_factory=list)
    cross_meeting_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of evidence segments across meetings (e.g. {'TS3006a': 2, 'TS3006c': 3})",
    )
