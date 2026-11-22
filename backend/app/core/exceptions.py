from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger, request_id_ctx

logger = get_logger("app.exceptions")


class AppException(Exception):
    """Base application exception for anticipated domain/service errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


def format_error_response(
    status_code: int,
    error_code: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[Any] = None,
) -> JSONResponse:
    """Build a standardized client-facing error payload."""
    payload: Dict[str, Any] = {
        "error": {
            "code": error_code,
            "message": message,
            "request_id": request_id or request_id_ctx.get(),
        }
    }
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            f"AppException: [{exc.error_code}] {exc.message} (status: {exc.status_code})"
        )
        return format_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning(f"HTTPException: {exc.detail} (status: {exc.status_code})")
        return format_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=str(exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(f"RequestValidationError on {request.url.path}: {exc.errors()}")
        return format_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=exc.errors(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log complete stack trace internally with request context
        logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
        # Return generic safe message to client without leaking internal details
        return format_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal error occurred. Please contact support with the request ID.",
        )
