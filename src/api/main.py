# src/api/main.py
import os
import re
import signal
import time
from typing import Any

import bleach
from dotenv import load_dotenv
from fastapi import (Body, FastAPI, File, HTTPException, Path, Query, Request,
                     UploadFile)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from logging_setup import setup_logging
from middleware.correlation import CorrelationIdMiddleware
from middleware.req_res import RequestResponseLoggingMiddleware
from middleware.validate_request import ValidateRequestMiddleware
from pydantic import BaseModel, EmailStr, Field, validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from validate_request import (safe_filename, sanitize_string,
                              validate_upload_file)

from api.validate_request import sanitize_string, validate_file

from .handlers import rate_limit_handler

# -------------------------
# Environment Setup
# -------------------------
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Default API")
APP_ENV = os.getenv("APP_ENV", "development")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

start_time = time.time()

# -------------------------
# Logging Setup
# -------------------------
logger = setup_logging(level=LOG_LEVEL)

# -------------------------
# Rate Limiting Setup
# -------------------------
limiter = Limiter(key_func=get_remote_address)  # per client IP
app = FastAPI(title=APP_NAME)
app = FastAPI()

# Attach middlewares
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestResponseLoggingMiddleware)
app.add_middleware(
    ValidateRequestMiddleware, allowed_types=("application/json",), max_body=2_000_000
)
# Handle 429 (Too Many Requests)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


# -------------------------
# Startup & Shutdown Events
# -------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 app_startup", environment=APP_ENV, version=APP_VERSION)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 app_shutdown", message="Application shutting down gracefully")


# -------------------------
# Safe Signal Handling
# -------------------------
shutting_down = False


def handle_exit(sig, frame):
    """Handle safe shutdown signals."""
    global shutting_down
    if not shutting_down:
        shutting_down = True
        logger.info(f"Received exit signal {sig}. Cleaning up...")


signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # Docker/K8s stop


# -------------------------
# Global Error Handlers
# -------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "path": request.url.path},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(
        "validation_error",
        errors=exc.errors(),
        body=exc.body,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "path": request.url.path},
    )


# -------------------------
# Routes
# -------------------------
users = [
    {"id": 1, "name": "Sai"},
    {"id": 2, "name": "kanchi"},
]

app = FastAPI()


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Run validation
    validate_file(file)

    # If valid, save or process
    return {"filename": file.filename, "status": "✅ File uploaded successfully"}


@app.get("/")
@limiter.limit("10/minute")  # max 10 requests/minute per IP
def read_root(request: Request) -> dict[str, str]:
    logger.info("root_called")
    return {"message": f"Welcome to {APP_NAME}"}


@app.get("/users")
@limiter.limit("5/minute")  # stricter: 5 requests/minute
def get_users(request: Request) -> list[dict[str, Any]]:
    logger.info("get_users", active_users=len(users))
    return users


@app.get("/users/{user_id}")
@limiter.limit("5/minute")
def get_user(request: Request, user_id: int = Path(..., ge=1)) -> dict[str, Any]:
    logger.info("get_user_request", user_id=user_id)
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/info")
@limiter.limit("20/minute")  # more relaxed: 20 requests/minute
def get_info(request: Request) -> dict[str, Any]:
    uptime = int(time.time() - start_time)
    logger.info("info_requested", uptime=uptime)
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "uptime_seconds": uptime,
    }


# -------------------------
# Input Validation & Sanitization
# -------------------------
NAME_RE = re.compile(r"^[A-Za-z0-9' \-\.]+$")  # allow safe characters


class DataInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Full name")
    age: int = Field(..., ge=0, le=120, description="Age must be between 0 and 120")
    email: EmailStr

    @validator("name")
    def validate_and_sanitize_name(cls, v: str) -> str:
        v = v.strip()
        if not NAME_RE.match(v):
            raise ValueError("Name contains invalid characters")
        return bleach.clean(v, strip=True)

    @validator("email")
    def normalize_email(cls, v: EmailStr) -> EmailStr:
        local, _, domain = str(v).partition("@")
        return f"{local}@{domain.lower()}"

    class Config:
        anystr_strip_whitespace = True


@app.post("/data")
@limiter.limit("3/minute")  # stricter on POST
def create_data(request: Request, data: DataInput = Body(...)) -> dict[str, Any]:
    sanitized = data.dict()
    logger.info("data_received", received=sanitized)
    return {
        "message": "Data received successfully",
        "received": sanitized,
    }


@app.post("/data")
def create_data(request: Request, data: DataInput = Body(...)):
    safe = {
        "name": sanitize_string(data.name),
        "age": data.age,
        "email": sanitize_string(data.email),
    }
    logger.info("data_received", received=safe)  # log sanitized version only

    # TODO: call DB save function with safe dict
    saved = db_service.save_user(safe)  # shown in next step
    return {"message": "ok", "saved": saved}


# Example file upload endpoint
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1) validate (type + size)
    await validate_upload_file(file)

    # 2) safe filename + write to uploads dir
    filename = safe_filename(file.filename)
    dest = os.path.join(UPLOAD_DIR, filename)
    with open(dest, "wb") as out:
        content = await file.read()  # careful with very large files; we validated size
        out.write(content)

    logger.info("file_saved", filename=filename)
    return {"filename": filename}


# at top of main.py
import db_service


# ensure init_db() called on startup if using sqlite3 init
@app.on_event("startup")
def startup_db():
    db_service.init_db()  # optional for sqlite example


@app.get("/")
def root():
    return {"message": "Welcome to the API!"}


@app.post("/data")
def post_data(data: dict):
    # Example sanitization
    sanitized_data = {
        k: sanitize_string(v) if isinstance(v, str) else v for k, v in data.items()
    }
    return {"received": sanitized_data}
