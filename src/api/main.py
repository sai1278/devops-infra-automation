import os
import time
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

app = FastAPI()

# Track uptime
start_time = time.time()

# Mock DB
users = [
    {"id": 1, "name": "Sai"},
    {"id": 2, "name": "kanchi"}
]

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}

@app.get("/users")
def get_users():
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ✅ GET /info endpoint
@app.get("/info")
def get_info():
    return {
        "app_name": "DevOps Infra Automation API",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development"),
        "uptime_seconds": int(time.time() - start_time)
    }

# ✅ POST /data endpoint
class DataInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Name must be 2–50 chars")
    age: int = Field(..., ge=0, le=120, description="Age must be between 0–120")
    email: str = Field(..., pattern=r'^\S+@\S+\.\S+$', description="Valid email address")

@app.post("/data")
def create_data(data: DataInput = Body(...)):
    return {
        "message": "Data received successfully",
        "received": data.dict()
    }
