import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

logger = structlog.get_logger()

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # prefer incoming header, else generate new UUID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # bind to contextvars so structlog includes it automatically
        bind_contextvars(correlation_id=correlation_id)

        # log request start
        logger.info("request_start", method=request.method, path=str(request.url))

        response: Response = None
        try:
            response = await call_next(request)
            return response
        finally:
            # attach correlation id to response header
            if response is not None:
                response.headers["X-Correlation-ID"] = correlation_id

            # log request end with status code
            logger.info("request_end", status_code=(response.status_code if response else None))
            # clear contextvars to avoid leaking to different tasks
            clear_contextvars()
