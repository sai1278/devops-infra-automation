# tests/test_endpoints.py
import pytest
from fastapi.testclient import TestClient

from api.main import app  # Corrected import

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]


def test_data_post_sanitization():
    payload = {"name": "<b>Sai</b>", "age": 25, "email": "test@example.com"}
    response = client.post("/data", json=payload)
    assert response.status_code == 200
    body = response.json()["received"]
    assert "<b>" not in body["name"]  # ✅ sanitized
