from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
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

