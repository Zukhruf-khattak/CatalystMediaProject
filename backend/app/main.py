from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.tracing import configure_tracing

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    settings = get_settings()

    # 1. Initialize structured logging
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"[env: {settings.app_env}, debug: {settings.debug}]"
    )

    # 2. Configure observability / tracing safely
    configure_tracing(settings)

    yield

    logger.info(f"Shutting down {settings.app_name} gracefully.")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Autonomous meeting intelligence, cross-meeting memory, and pre-meeting briefing agent.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Request ID Middleware (must run before exception handlers)
    application.add_middleware(RequestIDMiddleware)

    # 2. CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )

    # 3. Centralized Exception Handlers
    register_exception_handlers(application)

    # 4. API Route Controllers
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    # 5. Root service route
    @application.get(
        "/",
        tags=["System Information"],
        summary="Service root endpoint",
    )
    def root_endpoint() -> dict:
        return {
            "message": f"Welcome to {settings.app_name} API",
            "version": settings.app_version,
            "docs_url": "/docs",
            "health_url": f"{settings.api_v1_prefix}/health",
            "readiness_url": f"{settings.api_v1_prefix}/ready",
        }

    return application


app = create_application()
