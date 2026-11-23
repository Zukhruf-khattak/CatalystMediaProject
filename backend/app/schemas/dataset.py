import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ParsedSpeaker(BaseModel):
    """Parsed speaker record from transcript header."""

    model_config = ConfigDict(frozen=True)

    speaker_label: str = Field(..., description="Full label, e.g. 'Speaker A'")
    speaker_letter: str = Field(..., description="Single character, e.g. 'A'")
    role: Optional[str] = Field(
        None, description="Role if specified in header or introductory turn"
    )


class ParsedTurn(BaseModel):
    """Parsed individual speaker turn."""

    model_config = ConfigDict(frozen=True)

    turn_index: int = Field(..., ge=0, description="0-based sequential index")
    speaker_label: str = Field(..., description="Speaker label, e.g. 'Speaker A'")
    speaker_letter: str = Field(..., description="Speaker letter, e.g. 'A'")
    start_time_str: str = Field(..., description="HH:MM:SS format string")
    start_time_seconds: int = Field(..., ge=0, description="Total seconds from start")
    end_time_seconds: Optional[int] = Field(None, ge=0, description="Calculated end time")
    raw_text: str = Field(..., min_length=1, description="Verbatim transcript text")
    normalized_text: str = Field(..., description="Normalized text for lexical search")


class ParsedMeeting(BaseModel):
    """Complete parsed meeting document."""

    meeting_code: str = Field(..., description="e.g. 'ES2002a'")
    team_code: str = Field(..., description="e.g. 'ES2002'")
    meeting_number: Optional[int] = Field(None, ge=1, le=4, description="1 to 4")
    sequence_letter: Optional[str] = Field(None, description="'a', 'b', 'c', or 'd'")
    speakers: List[ParsedSpeaker] = Field(default_factory=list)
    turns: List[ParsedTurn] = Field(default_factory=list)
    source_filename: str = Field(..., description="Transcript filename")
    source_sha256: str = Field(..., description="SHA-256 hash of original file")
    word_count: int = Field(0, ge=0)
    total_turns: int = Field(0, ge=0)
    raw_text: str = Field(..., description="Exact raw file content")
    duration_seconds: Optional[float] = Field(None, ge=0.0)
    parser_warnings: List[str] = Field(default_factory=list)


class IngestionJobCreate(BaseModel):
    """Request options to launch an ingestion run."""

    force_reingest: bool = Field(
        default=False,
        description="Whether to overwrite existing ingested meetings",
    )
    skip_embeddings: bool = Field(
        default=False,
        description="Skip embedding generation for fast text-only ingestion",
    )
    limit_files: Optional[int] = Field(
        default=None,
        ge=1,
        description="Limit the number of files processed (for testing)",
    )


class IngestionJobResponse(BaseModel):
    """Response representation of an IngestionJob record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_files: int
    completed_meetings: int
    failed_meetings: int
    skipped_meetings: int
    total_turns: int
    total_words: int
    embedded_turns: int
    current_file: Optional[str] = None
    errors_json: List[Dict[str, Any]] = Field(default_factory=list)
    summary_json: Dict[str, Any] = Field(default_factory=dict)


class IngestionJobListResponse(BaseModel):
    """Paginated or listed ingestion jobs."""

    jobs: List[IngestionJobResponse]
    total_count: int


class IngestionStatsResponse(BaseModel):
    """High-level repository dataset statistics."""

    total_teams: int
    total_meetings: int
    total_speakers: int
    total_turns: int
    embedded_turns: int
    latest_job: Optional[IngestionJobResponse] = None
