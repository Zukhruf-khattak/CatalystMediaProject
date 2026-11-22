from typing import Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.health import HealthResponse, ReadyResponse

logger = get_logger("app.services.health")


class HealthService:
    """Business logic for system liveness and dependency readiness checks."""

    @staticmethod
    def get_health(settings: Settings) -> HealthResponse:
        """Return basic application process liveness."""
        return HealthResponse(
            status="healthy",
            app_name=settings.app_name,
            version=settings.app_version,
            environment=settings.app_env,
        )

    @staticmethod
    def check_readiness(session: Session, settings: Settings) -> Tuple[bool, ReadyResponse]:
        """
        Verify database connectivity using a short execution timeout.
        Returns a tuple of (is_healthy, ReadyResponse).
        """
        db_healthy = False
        try:
            # Short 5-second timeout probe
            session.execute(
                text("SELECT 1"),
                execution_options={"timeout": 5.0},
            )
            db_healthy = True
        except Exception as exc:
            logger.warning(f"Database readiness probe failed: {exc}")
            db_healthy = False

        status_str = "ready" if db_healthy else "degraded"
        response = ReadyResponse(
            status=status_str,
            database=db_healthy,
            app_name=settings.app_name,
            version=settings.app_version,
            environment=settings.app_env,
        )
        return db_healthy, response
