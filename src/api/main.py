# src/api/main.py
import os
import time
import signal
from fastapi import FastAPI, HTTPException, Body
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

app = FastAPI(title=APP_NAME)
app.add_middleware(CorrelationIdMiddleware)

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
# Optional: system signal handling (safe)
# -------------------------
# This logs signals without calling sys.exit()
def handle_exit(sig, frame):
    logger.info(f"Received exit signal {sig}. Cleaning up...")

signal.signal(signal.SIGINT, handle_exit)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # Docker/K8s stop

# -------------------------
# Routes
# -------------------------
users = [
    {"id": 1, "name": "Sai"},
    {"id": 2, "name": "kanchi"}
]

@app.get("/")
def read_root():
    logger.info("root_called")
    return {"message": f"Welcome to {APP_NAME}"}

@app.get("/users")
def get_users():
    logger.info("get_users", active_users=len(users))
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int):
    logger.info("get_user_request", user_id=user_id)
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/info")
def get_info():
    uptime = int(time.time() - start_time)
    logger.info("info_requested", uptime=uptime)
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "uptime_seconds": uptime
    }

class DataInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., ge=0, le=120)
    email: str = Field(..., pattern=r'^\S+@\S+\.\S+$')

@app.post("/data")
def create_data(data: DataInput = Body(...)):
    logger.info("data_received", received=data.dict())
    return {"message": "Data received successfully", "received": data.dict()}
