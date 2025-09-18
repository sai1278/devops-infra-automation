# src/api/main.py
import os
import time
import signal
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from middleware.req_res import RequestResponseLoggingMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load env vars
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Default API")
APP_ENV = os.getenv("APP_ENV", "development")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

start_time = time.time()

# logging setup
from logging_setup import setup_logging
from middleware.correlation import CorrelationIdMiddleware
import structlog

logger = setup_logging(level=LOG_LEVEL)

# -------------------------
# Rate Limiting Setup
# -------------------------
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)  # per client IP
app = FastAPI(title=APP_NAME)

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

signal.signal(signal.SIGINT, handle_exit)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # Docker/K8s stop

# -------------------------
# Global Error Handlers
# -------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("http_exception", status_code=exc.status_code, detail=exc.detail, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "path": request.url.path},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("validation_error", errors=exc.errors(), body=exc.body, path=request.url.path)
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors(), "path": request.url.path},
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
    {"id": 2, "name": "kanchi"}
]

@app.get("/")
@limiter.limit("10/minute")   # max 10 requests/minute per IP
def read_root(request: Request):
    try:
        logger.info("root_called")
        return {"message": f"Welcome to {APP_NAME}"}
    except Exception as e:
        logger.exception("root_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load root endpoint")

@app.get("/users")
@limiter.limit("5/minute")   # stricter: 5 requests/minute
def get_users(request: Request):
    try:
        logger.info("get_users", active_users=len(users))
        return users
    except Exception as e:
        logger.exception("get_users_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Could not fetch users")

@app.get("/users/{user_id}")
@limiter.limit("5/minute")
def get_user(request: Request, user_id: int):
    try:
        logger.info("get_user_request", user_id=user_id)
        user = next((u for u in users if u["id"] == user_id), None)
        if not user:
            logger.warning("user_not_found", user_id=user_id)
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_user_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Could not fetch user")

@app.get("/info")
@limiter.limit("20/minute")   # more relaxed: 20 requests/minute
def get_info(request: Request):
    try:
        uptime = int(time.time() - start_time)
        logger.info("info_requested", uptime=uptime)
        return {
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "environment": APP_ENV,
            "uptime_seconds": uptime
        }
    except Exception as e:
        logger.exception("info_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Could not fetch app info")

class DataInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., ge=0, le=120)
    email: str = Field(..., pattern=r'^\S+@\S+\.\S+$')

@app.post("/data")
@limiter.limit("3/minute")   # stricter on POST
def create_data(request: Request, data: DataInput = Body(...)):
    try:
        logger.info("data_received", received=data.dict())
        return {"message": "Data received successfully", "received": data.dict()}
    except Exception as e:
        logger.exception("data_processing_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Could not process data")
