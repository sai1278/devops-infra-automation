# src/api/main.py
import os
import signal
import time

from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Load env vars
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Default API")
APP_ENV = os.getenv("APP_ENV", "development")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

start_time = time.time()

import structlog
# logging setup
from logging_setup import setup_logging
from middleware.correlation import CorrelationIdMiddleware
from middleware.req_res import RequestResponseLoggingMiddleware

logger = setup_logging(level=LOG_LEVEL)

# -------------------------
# Rate Limiting Setup
# -------------------------
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# -------------------------
# App Setup with Metadata
# -------------------------
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="""
    🚀 **API Documentation**

    This API provides:
    - User management (`/users`, `/users/{user_id}`)
    - App info and health check (`/`, `/info`)
    - Data submission (`/data`)
    - Built-in rate limiting, correlation IDs, and structured logging
    """,
    contact={
        "name": "API Support",
        "url": "https://github.com/your-org/your-repo",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Attach middlewares
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestResponseLoggingMiddleware)

# Handle 429 (Too Many Requests)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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
    global shutting_down
    if not shutting_down:
        shutting_down = True
        logger.info(f"Received exit signal {sig}. Cleaning up...")


signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


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
        "validation_error", errors=exc.errors(), body=exc.body, path=request.url.path
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
users = [{"id": 1, "name": "Sai"}, {"id": 2, "name": "kanchi"}]


@app.get(
    "/",
    summary="Root Endpoint",
    description="Returns a welcome message with the application name.",
    tags=["General"],
    responses={200: {"description": "Successful Response"}},
)
@limiter.limit("10/minute")
def read_root(request: Request):
    logger.info("root_called")
    return {"message": f"Welcome to {APP_NAME}"}


@app.get(
    "/users",
    summary="Get All Users",
    description="Fetches a list of all users.",
    tags=["Users"],
    responses={200: {"description": "List of users"}},
)
@limiter.limit("5/minute")
def get_users(request: Request):
    logger.info("get_users", active_users=len(users))
    return users


@app.get(
    "/users/{user_id}",
    summary="Get User by ID",
    description="Fetch details of a specific user by their ID.",
    tags=["Users"],
    responses={
        200: {"description": "User details"},
        404: {"description": "User not found"},
    },
)
@limiter.limit("5/minute")
def get_user(request: Request, user_id: int):
    logger.info("get_user_request", user_id=user_id)
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get(
    "/info",
    summary="Application Info",
    description="Returns app name, version, environment, and uptime.",
    tags=["General"],
)
@limiter.limit("20/minute")
def get_info(request: Request):
    uptime = int(time.time() - start_time)
    logger.info("info_requested", uptime=uptime)
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "uptime_seconds": uptime,
    }


class DataInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User's name")
    age: int = Field(..., ge=0, le=120, description="User's age (0-120)")
    email: str = Field(
        ..., pattern=r"^\S+@\S+\.\S+$", description="Valid email address"
    )


@app.post(
    "/data",
    summary="Submit Data",
    description="Accepts user data (name, age, email) and returns confirmation.",
    tags=["Data"],
    responses={
        200: {"description": "Data received successfully"},
        422: {"description": "Validation error"},
    },
)
@limiter.limit("3/minute")
def create_data(request: Request, data: DataInput = Body(...)):
    logger.info("data_received", received=data.dict())
    return {"message": "Data received successfully", "received": data.dict()}
