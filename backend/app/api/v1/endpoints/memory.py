import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dataset import Meeting, Team
from app.models.memory import MemoryExtractionRun
from app.schemas.memory import (
    MemoryExtractionRequest,
    MemoryExtractionRunResponse,
    MemoryResponse,
    MemorySearchFilter,
    MemorySearchResponse,
)
from app.services.memory_extraction_service import (
    MemoryExtractionService,
)
from app.services.memory_retrieval_service import MemoryRetrievalService

router = APIRouter(prefix="/memory", tags=["Temporal Memory"])


@router.post(
    "/extract",
    response_model=MemoryExtractionRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger temporal memory extraction for a meeting or team",
)
def extract_memories(
    request: MemoryExtractionRequest,
    db: Session = Depends(get_db),
) -> MemoryExtractionRunResponse:
    """Extract and validate temporal memories from meeting transcripts."""
    service = MemoryExtractionService(db=db, extraction_version=request.extraction_version)

    if request.meeting_code:
        meeting = db.execute(
            select(Meeting).where(Meeting.meeting_code == request.meeting_code)
        ).scalar_one_or_none()
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meeting '{request.meeting_code}' not found.",
            )
        run = service.extract_memories_for_meeting(meeting_id=meeting.id, force=request.force)
        return MemoryExtractionRunResponse.model_validate(run)

    elif request.team_code:
        team = db.execute(
            select(Team).where(Team.team_code == request.team_code)
        ).scalar_one_or_none()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team '{request.team_code}' not found.",
            )
        runs = service.extract_memories_for_team(team_code=request.team_code, force=request.force)
        if not runs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No meetings found for team '{request.team_code}'.",
            )
        # Return the final run in the series
        return MemoryExtractionRunResponse.model_validate(runs[-1])

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either 'meeting_code' or 'team_code'.",
        )


@router.get(
    "/runs/{run_id}",
    response_model=MemoryExtractionRunResponse,
    summary="Get status and metrics of a memory extraction run",
)
def get_extraction_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> MemoryExtractionRunResponse:
    """Retrieve audit details for an extraction run."""
    run = db.get(MemoryExtractionRun, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction run '{run_id}' not found.",
        )
    return MemoryExtractionRunResponse.model_validate(run)


@router.get(
    "/search",
    response_model=MemorySearchResponse,
    summary="Search and filter temporal memories",
)
def search_memories(
    team_code: Optional[str] = Query(None, description="Team code, e.g. TS3006"),
    meeting_code: Optional[str] = Query(None, description="Meeting code, e.g. TS3006a"),
    meeting_order: Optional[int] = Query(None, ge=1, le=4, description="Meeting order (1-4)"),
    sequence_letter: Optional[str] = Query(None, description="Meeting letter (a-d)"),
    memory_type: Optional[str] = Query(None, description="DECISION, ACTION, PREFERENCE, etc."),
    memory_status: Optional[str] = Query(
        None, alias="status", description="current, superseded, open, resolved"
    ),
    query_text: Optional[str] = Query(
        None, description="Lexical search in statement and quotation"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> MemorySearchResponse:
    """Query temporal memories with multidimensional filtering and pagination."""
    filter_params = MemorySearchFilter(
        team_code=team_code,
        meeting_code=meeting_code,
        meeting_order=meeting_order,
        sequence_letter=sequence_letter,
        memory_type=memory_type,
        status=memory_status,
        query_text=query_text,
        limit=limit,
        offset=offset,
    )
    retrieval_service = MemoryRetrievalService(db=db)
    items, total_count = retrieval_service.search_memories(filter_params)

    return MemorySearchResponse(
        items=[MemoryResponse.model_validate(item) for item in items],
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Get memory item by ID with full evidence and relationship graph",
)
def get_memory(
    memory_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> MemoryResponse:
    """Retrieve single memory record by unique identifier."""
    retrieval_service = MemoryRetrievalService(db=db)
    memory = retrieval_service.get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record '{memory_id}' not found.",
        )
    return MemoryResponse.model_validate(memory)
