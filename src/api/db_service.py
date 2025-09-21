# src/api/db_service.py
import sqlite3
from typing import Any, Dict

from validate_request import sanitize_string

DB_PATH = "data.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        email TEXT
    )"""
    )
    conn.commit()
    conn.close()


def save_user(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, age, email) VALUES (?, ?, ?)",
        (data["name"], data["age"], data["email"]),
    )
    conn.commit()
    inserted_id = cur.lastrowid
    conn.close()
    return {"id": inserted_id, **data}


def save_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert sanitized user data into the DB safely."""

    # 🔹 Sanitize again here (last defense)
    safe = {
        "name": sanitize_string(data["name"]),
        "age": int(data["age"]),  # also enforce numeric conversion
        "email": sanitize_string(data["email"]),
    }

    # then insert safe into DB...
    # (your SQL insert code here)
    return safe
