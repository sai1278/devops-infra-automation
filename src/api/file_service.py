import os

from validate_request import sanitize_string


def save_file(filename: str, content: bytes) -> str:
    """Save uploaded file securely."""
    # 🔹 Sanitize filename
    safe_filename = sanitize_string(os.path.basename(filename))
    path = f"uploads/{safe_filename}"
    with open(path, "wb") as f:
        f.write(content)
    return path
