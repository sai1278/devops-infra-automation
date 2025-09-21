# src/api/validate_request.py

import bleach


def sanitize_string(value: str) -> str:
    """Sanitize input string using bleach."""
    return bleach.clean(value)
