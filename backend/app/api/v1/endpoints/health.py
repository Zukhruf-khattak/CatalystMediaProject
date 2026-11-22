from fastapi import APIRouter, Depends, status

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application liveness probe",
    description="Returns basic application process health without exposing sensitive configuration.",
)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthService.get_health(settings)
