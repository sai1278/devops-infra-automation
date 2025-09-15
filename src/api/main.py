# src/api/main.py
import os
import time
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

# logging imports
from logging_setup import setup_logging
from middleware.correlation import CorrelationIdMiddleware
import structlog

# setup structured logging (returns a structlog logger)
logger = setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title=os.getenv("APP_NAME", "DevOps Infra Automation API"))
app.add_middleware(CorrelationIdMiddleware)

# Uptime tracking
start_time = time.time()

# Mock DB
users = [
    {"id": 1, "name": "Sai"},
    {"id": 2, "name": "kanchi"}
]

@app.get("/")
def read_root():
    logger.info("root_called")
    return {"message": "Welcome to FastAPI!"}

@app.get("/users")
def get_users():
    logger.info("get_users", active_users=len(users))
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int):
    logger.info("get_user_request", user_id=user_id)
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        logger.warn("user_not_found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/info")
def get_info():
    uptime = int(time.time() - start_time)
    logger.info("info_requested", uptime=uptime)
    return {
        "app_name": os.getenv("APP_NAME", "DevOps Infra Automation API"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("APP_ENV", "development"),
        "uptime_seconds": uptime
    }

# Example POST /data model (if you already have it)
class DataInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., ge=0, le=120)
    email: str = Field(..., pattern=r'^\S+@\S+\.\S+$')

@app.post("/data")
def create_data(data: DataInput = Body(...)):
    logger.info("data_received", received=data.dict())
    return {"message": "Data received successfully", "received": data.dict()}
