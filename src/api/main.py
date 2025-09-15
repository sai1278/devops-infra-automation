import os
import time
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Track uptime
start_time = time.time()

# Mock DB (already in your code)
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

# ✅ New endpoint: /info
@app.get("/info")
def get_info():
    return {
        "app_name": "DevOps Infra Automation API",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development"),
        "uptime_seconds": int(time.time() - start_time)
    }
