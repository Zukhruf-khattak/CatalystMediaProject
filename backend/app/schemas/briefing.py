"""Pydantic v2 schemas for Team Pre-Meeting Briefings."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BriefingCitation(BaseModel):
    """Citation supporting a factual bullet point in the briefing."""

    meeting_id: str = Field(..., description="Referenced meeting code (e.g. TS3012a)")
    quote: str = Field(..., description="Exact quotation of >= 6 words")
    speaker_label: Optional[str] = Field(None, description="Speaker label (e.g. Speaker A)")
    speaker_role: Optional[str] = Field(None, description="Speaker role if supported by metadata")
    turn_id: Optional[str] = Field(None, description="Referenced speaker turn UUID")
    turn_index: Optional[int] = Field(None, description="Speaker turn index in meeting")


class TimelineMeetingItem(BaseModel):
    """Chronological summary item for a specific meeting in the timeline."""

    meeting_code: str = Field(..., description="Meeting code (e.g. TS3012a)")
    sequence_letter: str = Field(..., description="Meeting sequence letter (a, b, c, d)")
    meeting_order: int = Field(..., description="Chronological meeting order (1, 2, 3...)")
    discussion_topics: List[str] = Field(
        default_factory=list, description="Main topics discussed in this meeting"
    )
    major_decisions: List[str] = Field(
        default_factory=list, description="Major decisions reached in this meeting"
    )
    significant_changes: List[str] = Field(
        default_factory=list, description="Changes relative to earlier meetings"
    )
    open_actions: List[str] = Field(
        default_factory=list, description="Actions and commitments recorded"
    )
    citations: List[BriefingCitation] = Field(
        default_factory=list, description="Supporting verbatim transcript citations"
    )


class DecisionItem(BaseModel):
    """A current or latest confirmed decision."""

    statement: str = Field(..., description="Confirmed decision statement")
    meeting_id: str = Field(..., description="Meeting where decision was established")
    speaker_label: Optional[str] = Field(None, description="Speaker who proposed or confirmed")
    speaker_role: Optional[str] = Field(None, description="Speaker functional role")
    quote: str = Field(..., description="Exact supporting quotation of >= 6 words")
    status: str = Field("CURRENT", description="Decision status: CURRENT, SUPERSEDED, PROPOSED")
    replaces_statement: Optional[str] = Field(
        None, description="Earlier decision replaced by this decision"
    )
    replaces_meeting_id: Optional[str] = Field(
        None, description="Meeting of the earlier replaced decision"
    )
    turn_id: Optional[str] = Field(None, description="Source turn UUID")


class DecisionChangeItem(BaseModel):
    """Evolution of a decision across meetings."""

    previous_decision: str = Field(..., description="Historical decision statement")
    updated_decision: str = Field(..., description="Updated or superseding decision statement")
    previous_meeting_id: str = Field(..., description="Meeting of the earlier decision")
    updated_meeting_id: str = Field(..., description="Meeting where the change occurred")
    previous_quote: str = Field(..., description="Verbatim quote supporting previous decision")
    updated_quote: str = Field(..., description="Verbatim quote supporting updated decision")
    reason: Optional[str] = Field(
        None, description="Explicitly supported rationale for the decision change"
    )
    turn_id_previous: Optional[str] = Field(None, description="Turn ID of previous decision")
    turn_id_updated: Optional[str] = Field(None, description="Turn ID of updated decision")


class ActionItem(BaseModel):
    """Outstanding task or commitment."""

    description: str = Field(..., description="Action or commitment description")
    owner: str = Field(
        "Unknown / Unassigned",
        description="Assigned owner (explicitly supported name, or 'Unknown / Unassigned')",
    )
    owner_confidence: str = Field(
        "EXPLICIT", description="Confidence level: EXPLICIT, UNKNOWN, UNCERTAIN"
    )
    source_meeting_id: str = Field(..., description="Meeting where action was assigned")
    speaker_label: Optional[str] = Field(None, description="Speaker who assigned or committed")
    status: str = Field("OPEN", description="Action status: OPEN, COMPLETED, IN_PROGRESS")
    quote: str = Field(..., description="Exact supporting quotation of >= 6 words")
    turn_id: Optional[str] = Field(None, description="Source turn UUID")


class DisagreementItem(BaseModel):
    """An issue or point of friction within the team."""

    disputed_issue: str = Field(..., description="Core issue or question disputed")
    positions: List[str] = Field(
        default_factory=list, description="Different positions or proposals expressed"
    )
    speakers_involved: List[str] = Field(
        default_factory=list, description="Speakers associated with competing positions"
    )
    supporting_evidence: List[str] = Field(
        default_factory=list, description="Evidence excerpts backing the disagreement"
    )
    resolution_status: str = Field(
        "UNRESOLVED", description="Status: UNRESOLVED, RESOLVED, REOPENED"
    )
    citations: List[BriefingCitation] = Field(
        default_factory=list, description="Supporting verbatim transcript citations"
    )


class BriefingGenerateRequest(BaseModel):
    """Request payload to generate a pre-meeting briefing."""

    team_code: str = Field("TS3012", min_length=2, max_length=32, description="Target team code")
    target_meeting_code: Optional[str] = Field(
        None,
        description="Meeting before which briefing is given (e.g. TS3012d). If omitted, defaults to before final meeting.",
    )
    regenerate: bool = Field(
        False, description="Whether to recompute and create a new version even if one exists"
    )


class BriefingResponse(BaseModel):
    """Structured response payload for a pre-meeting briefing."""

    id: uuid.UUID = Field(..., description="Unique briefing UUID")
    team_code: str = Field(..., description="Team code")
    target_meeting_code: Optional[str] = Field(
        None, description="Target upcoming meeting (e.g. TS3012d)"
    )
    version: int = Field(..., description="Briefing version number (1, 2, 3...)")
    title: str = Field(..., description="Briefing title")
    content_markdown: str = Field(..., description="Full 9-section Markdown briefing document")
    structured_payload: Dict[str, Any] = Field(
        default_factory=dict, description="Structured parsed sections and items"
    )
    validation_status: str = Field(
        "PASSED", description="Citation validation status (PASSED, FAILED, WARNING)"
    )
    validation_errors: List[str] = Field(
        default_factory=list, description="Validation issues if any"
    )
    citations_count: int = Field(0, description="Total number of citations in briefing")
    meetings_covered: List[str] = Field(
        default_factory=list, description="Chronological list of meetings covered"
    )
    generation_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Execution telemetry and timestamps"
    )
    created_at: datetime = Field(..., description="Creation timestamp")


class BriefingListResponse(BaseModel):
    """List of briefing versions for a team."""

    briefings: List[BriefingResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total briefing records found")
