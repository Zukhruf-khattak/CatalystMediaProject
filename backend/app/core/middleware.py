import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, request_id_ctx

logger = get_logger("app.middleware")

# Pattern for safe alphanumeric, hyphen, underscore request IDs (e.g. UUID)
SAFE_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9\-_]{1,64}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request has a tracking ID.
    Accepts an incoming X-Request-ID header if valid, otherwise generates a UUIDv4.
    Injects the ID into the contextvars context and returns it in the response header.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get("X-Request-ID")
        if incoming_id and SAFE_REQUEST_ID_REGEX.match(incoming_id):
            request_id = incoming_id
        else:
            request_id = str(uuid.uuid4())

        # Set contextvar for structured logging
        token = request_id_ctx.set(request_id)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
            return response
        finally:
            request_id_ctx.reset(token)
