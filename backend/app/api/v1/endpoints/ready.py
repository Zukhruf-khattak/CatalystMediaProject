from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.health import ReadyResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ReadyResponse,
            "description": "All dependencies are operational",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadyResponse,
            "description": "One or more dependencies are unavailable",
        },
    },
    summary="Dependency readiness probe",
    description="Verifies database connectivity with a bounded timeout probe.",
)
def get_ready(
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReadyResponse:
    is_healthy, ready_data = HealthService.check_readiness(db, settings)
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ready_data
