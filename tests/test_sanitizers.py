# tests/test_sanitizers.py
import pytest

from api.validate_request import sanitize_string  # Corrected import


def test_sanitize_string_removes_tags():
    raw = "<script>alert('x')</script>"
    cleaned = sanitize_string(raw)
    assert "<script>" not in cleaned
    assert "alert('x')" in cleaned


def test_sanitize_string_keeps_text():
    raw = "Hello World"
    cleaned = sanitize_string(raw)
    assert cleaned == raw
