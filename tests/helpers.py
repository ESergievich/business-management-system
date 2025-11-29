import uuid


def unique_email(prefix: str) -> str:
    """Generate a unique email address."""
    return f"{prefix}_{uuid.uuid4().hex}@example.com"


def unique_string(prefix: str, length: int = 8) -> str:
    """Generate a unique string."""
    return f"{prefix}_{uuid.uuid4().hex[:length]}"
