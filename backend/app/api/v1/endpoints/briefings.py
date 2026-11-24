"""FastAPI endpoints for generating, validating, and retrieving Pre-Meeting Briefings."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.briefing import (
    BriefingGenerateRequest,
    BriefingListResponse,
    BriefingResponse,
)
from app.services.briefing_service import BriefingService

logger = get_logger("app.api.v1.briefings")
router = APIRouter(prefix="/briefings", tags=["briefings"])


@router.post(
    "/generate",
    response_model=BriefingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate pre-meeting briefing for a team",
    description=(
        "Analyzes chronological meeting history, extracts current and superseded decisions, "
        "tracks open actions and owners, surfaces unresolved disagreements, and verifies all citations."
    ),
)
def generate_team_briefing(
    request: BriefingGenerateRequest,
    db: Session = Depends(get_db),
) -> BriefingResponse:
    """Generate or retrieve a pre-meeting briefing for the specified team."""
    service = BriefingService(db=db)
    return service.generate_briefing(
        team_code=request.team_code,
        target_meeting_code=request.target_meeting_code,
        regenerate=request.regenerate,
    )


@router.get(
    "/ts3012",
    response_model=BriefingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest pre-meeting briefing for Team TS3012",
    description="Convenience endpoint returning the latest verified briefing for Team TS3012.",
)
def get_ts3012_briefing(
    regenerate: bool = Query(
        False, description="Whether to regenerate the briefing rather than return cached version"
    ),
    db: Session = Depends(get_db),
) -> BriefingResponse:
    """Retrieve or generate the Team TS3012 pre-meeting briefing."""
    service = BriefingService(db=db)
    if regenerate:
        return service.generate_briefing(
            team_code="TS3012", target_meeting_code="TS3012d", regenerate=True
        )
    existing = service.get_latest_briefing(team_code="TS3012")
    if existing:
        return existing
    # If not yet generated, generate initial version
    return service.generate_briefing(
        team_code="TS3012", target_meeting_code="TS3012d", regenerate=False
    )


@router.get(
    "/{team_code}/latest",
    response_model=BriefingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest briefing for a team",
)
def get_latest_team_briefing(
    team_code: str,
    target_meeting_code: Optional[str] = Query(None, description="Optional target meeting code"),
    db: Session = Depends(get_db),
) -> BriefingResponse:
    """Retrieve the highest version pre-meeting briefing for a team."""
    service = BriefingService(db=db)
    briefing = service.get_latest_briefing(
        team_code=team_code, target_meeting_code=target_meeting_code
    )
    if not briefing:
        # Generate on demand if not yet generated
        briefing = service.generate_briefing(
            team_code=team_code, target_meeting_code=target_meeting_code
        )
    return briefing


@router.get(
    "/{team_code}/versions",
    response_model=BriefingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all briefing versions for a team",
)
def list_briefing_versions(
    team_code: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BriefingListResponse:
    """List historical and current briefing versions for a team."""
    service = BriefingService(db=db)
    records = service.list_briefing_versions(team_code=team_code, limit=limit)
    return BriefingListResponse(briefings=records, total=len(records))


@router.get(
    "/{briefing_id}",
    response_model=BriefingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get briefing by unique ID",
)
def get_briefing_by_id(
    briefing_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> BriefingResponse:
    """Retrieve a specific briefing record by UUID."""
    service = BriefingService(db=db)
    briefing = service.get_briefing_by_id(briefing_id=briefing_id)
    if not briefing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Briefing with ID '{briefing_id}' was not found.",
        )
    return briefing
