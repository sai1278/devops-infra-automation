# src/api/middleware/validate_request.py
import html
import os
import re
import uuid
from typing import Tuple

from fastapi import HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE_MB = 5  # 5 MB


def sanitize_string(value: str) -> str:
    """Sanitize user input string to prevent XSS or log injection."""
    value = value.strip()
    value = html.escape(value)  # encode <, >, &
    value = re.sub(r"[\r\n\t]", " ", value)  # remove log-breaking chars
    return value


# make an upload-safe filename and avoid path traversal
def safe_filename(filename: str) -> str:
    """Return a safe filename: basename + random prefix to avoid collisions."""
    name = os.path.basename(filename)  # drop any path
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)  # allow limited chars
    unique = uuid.uuid4().hex[:8]
    return f"{unique}_{name}"


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file for type, extension, and size."""

    # 1. Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"❌ Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 2. Validate size
    file.file.seek(0, os.SEEK_END)  # Move cursor to end
    size = file.file.tell() / (1024 * 1024)  # Size in MB
    file.file.seek(0)  # Reset cursor

    if size > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"❌ File too large. Max size: {MAX_FILE_SIZE_MB} MB",
        )


class ValidateRequestMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app, allowed_types=("application/json",), max_body: int = 1024 * 1024
    ):
        super().__init__(app)
        self.allowed_types = allowed_types
        self.max_body = max_body

    async def dispatch(self, request: Request, call_next):
        content_type = request.headers.get("content-type", "").split(";")[0]
        if content_type and content_type not in self.allowed_types:
            return JSONResponse(
                status_code=415, content={"error": "Unsupported Media Type"}
            )

        cl = request.headers.get("content-length")
        if cl and int(cl) > self.max_body:
            return JSONResponse(status_code=413, content={"error": "Payload Too Large"})

        # If no content-length header, we could optionally read and check the body (costly)
        return await call_next(request)
