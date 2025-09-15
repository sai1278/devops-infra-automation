from fastapi import FastAPI, HTTPException
import time

app = FastAPI()

# Track start time for uptime
start_time = time.time()
VERSION = "1.0.0"

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

@app.get("/health")
def health_check():
    uptime = round(time.time() - start_time, 2)
    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "version": VERSION
    }
