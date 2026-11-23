import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal, get_db
from app.schemas.dataset import (
    IngestionJobCreate,
    IngestionJobListResponse,
    IngestionJobResponse,
    IngestionStatsResponse,
)
from app.services.ingestion_service import IngestionService

logger = get_logger("app.api.v1.ingestion")
router = APIRouter(prefix="/ingestion", tags=["Dataset Ingestion & Indexing"])


def run_background_ingestion(job_options: IngestionJobCreate) -> None:
    """Execute ingestion in background worker thread with dedicated DB session."""
    db: Session = SessionLocal()
    try:
        service = IngestionService(db=db)
        service.run_ingestion(options=job_options)
    except Exception as e:
        logger.error(f"Background ingestion failed: {e}")
    finally:
        db.close()


@router.post(
    "/jobs",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Launch a transcript ingestion job",
    description="Trigger batch ingestion of AMI transcripts, including parsing, persistence, and local embeddings.",
)
def create_ingestion_job(
    job_in: IngestionJobCreate,
    background_tasks: BackgroundTasks,
    sync: bool = Query(
        default=False,
        description="If True, execute synchronously before returning response (useful for tests/CLI)",
    ),
    db: Session = Depends(get_db),
) -> IngestionJobResponse:
    service = IngestionService(db=db)

    if sync:
        # Synchronous execution
        job_result = service.run_ingestion(options=job_in)
        return job_result
    else:
        # Asynchronous background execution
        # Create pending job record first so client immediately receives valid job ID
        job = IngestionJobResponse(
            id=uuid.uuid4(),
            status="PENDING",
            started_at=datetime.now(timezone.utc),
            total_files=0,
            completed_meetings=0,
            failed_meetings=0,
            skipped_meetings=0,
            total_turns=0,
            total_words=0,
            embedded_turns=0,
            errors_json=[],
            summary_json={"queued": True},
        )
        background_tasks.add_task(run_background_ingestion, job_in)
        return job


@router.get(
    "/jobs/{job_id}",
    response_model=IngestionJobResponse,
    summary="Get ingestion job details",
    description="Retrieve status, progress, error logs, and metrics for a specific ingestion job.",
)
def get_ingestion_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> IngestionJobResponse:
    service = IngestionService(db=db)
    job = service.get_job(job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{job_id}' not found",
        )
    return job


@router.get(
    "/jobs",
    response_model=IngestionJobListResponse,
    summary="List recent ingestion jobs",
    description="Retrieve a list of past ingestion runs with status and metrics.",
)
def list_ingestion_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> IngestionJobListResponse:
    service = IngestionService(db=db)
    jobs = service.list_jobs(limit=limit)
    return IngestionJobListResponse(jobs=jobs, total_count=len(jobs))


@router.get(
    "/stats",
    response_model=IngestionStatsResponse,
    summary="Get dataset and index statistics",
    description="Return total count of ingested teams, meetings, speakers, turns, and dense embeddings.",
)
def get_dataset_stats(
    db: Session = Depends(get_db),
) -> IngestionStatsResponse:
    service = IngestionService(db=db)
    return service.get_stats()
