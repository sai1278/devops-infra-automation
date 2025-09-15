from fastapi import FastAPI, HTTPException
import time, os, psutil   # psutil for system metrics

app = FastAPI()

# Track start time
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

@app.get("/metrics")
def metrics():
    uptime = round(time.time() - start_time, 2)
    process = psutil.Process(os.getpid())  # current process stats

    return {
        "uptime_seconds": uptime,
        "version": VERSION,
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
        "active_users": len(users)
    }
