import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware

# Create a custom logger for request/response
logger = logging.getLogger("req_res")
logger.setLevel(logging.INFO)

# Add handler if not already added (to avoid duplicates in reload mode)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"➡️ Request: {request.method} {request.url}")

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"⬅️ Response: status={response.status_code} completed_in={process_time:.2f}ms"
        )

        return response
