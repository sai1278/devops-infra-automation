import logging
import time
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Create a custom logger for request/response
logger = logging.getLogger("req_res")
logger.setLevel(logging.INFO)

# Add handler if not already added (to avoid duplicates in reload mode)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time: float = time.time()

        logger.info(f"➡️ Request: {request.method} {request.url}")

        response: Response = await call_next(request)

        process_time: float = (time.time() - start_time) * 1000
        logger.info(
            f"⬅️ Response: status={response.status_code} "
            f"completed_in={process_time:.2f}ms"
        )

        return response
