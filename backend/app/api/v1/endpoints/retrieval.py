import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.dataset import TranscriptTurn
from app.schemas.retrieval import EvidencePackResponse, ProcessedQuery, RetrievalRequest
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.services.query_processor import get_query_processor

router = APIRouter(prefix="/retrieval", tags=["Hybrid Retrieval"])


class ProcessQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Query string to parse")


@router.post(
    "/search",
    response_model=EvidencePackResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute hybrid cross-meeting retrieval with RRF rank fusion",
)
def execute_hybrid_search(
    request: RetrievalRequest,
    db: Session = Depends(get_db),
) -> EvidencePackResponse:
    """Execute keyword, vector, or hybrid retrieval and assemble unified evidence pack."""
    service = HybridRetrievalService(db=db)
    try:
        return service.execute_retrieval(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {str(e)}",
        )


@router.post(
    "/process-query",
    response_model=ProcessedQuery,
    status_code=status.HTTP_200_OK,
    summary="Parse natural-language query to extract entities, teams, and search terms",
)
def process_query(
    request: ProcessQueryRequest,
) -> ProcessedQuery:
    """Extract team codes, meeting codes, speaker references, topics, and temporal intent."""
    processor = get_query_processor()
    return processor.process_query(request.query)


@router.get(
    "/turns/{turn_id}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve a transcript turn and surrounding context turns for citation verification",
)
def get_transcript_turn_context(
    turn_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve target turn and preceding/succeeding turns for contextual citation inspection."""
    stmt = (
        select(TranscriptTurn)
        .options(joinedload(TranscriptTurn.speaker), joinedload(TranscriptTurn.meeting))
        .where(TranscriptTurn.id == turn_id)
    )
    target = db.execute(stmt).scalars().first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript turn '{turn_id}' not found.",
        )

    # Get surrounding context turns
    before_stmt = (
        select(TranscriptTurn)
        .options(joinedload(TranscriptTurn.speaker))
        .where(
            TranscriptTurn.meeting_id == target.meeting_id,
            TranscriptTurn.turn_index < target.turn_index,
        )
        .order_by(TranscriptTurn.turn_index.desc())
        .limit(2)
    )
    before_turns = list(reversed(list(db.execute(before_stmt).scalars().all())))

    after_stmt = (
        select(TranscriptTurn)
        .options(joinedload(TranscriptTurn.speaker))
        .where(
            TranscriptTurn.meeting_id == target.meeting_id,
            TranscriptTurn.turn_index > target.turn_index,
        )
        .order_by(TranscriptTurn.turn_index.asc())
        .limit(2)
    )
    after_turns = list(db.execute(after_stmt).scalars().all())

    def serialize_turn(t: TranscriptTurn, is_target: bool = False):
        spk = t.speaker.speaker_label if t.speaker else f"Speaker {t.turn_index}"
        role = t.speaker.role if t.speaker else None
        return {
            "id": str(t.id),
            "turn_index": t.turn_index,
            "meeting_id": target.meeting.meeting_code if target.meeting else "Unknown",
            "speaker_label": spk,
            "speaker_role": role,
            "start_time": t.start_time_str or f"{t.start_time_seconds}s",
            "raw_text": t.raw_text,
            "is_target": is_target,
        }

    context = (
        [serialize_turn(t, is_target=False) for t in before_turns]
        + [serialize_turn(target, is_target=True)]
        + [serialize_turn(t, is_target=False) for t in after_turns]
    )

    return {
        "turn": serialize_turn(target, is_target=True),
        "context": context,
    }
