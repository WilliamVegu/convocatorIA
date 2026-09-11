"""Password hashing and validation adapter using bcrypt."""
from __future__ import annotations

import re
import bcrypt


def validate_password_complexity(password: str) -> None:
    """
    Validate corporate password policy:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una letra minúscula.")
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe contener al menos un dígito numérico.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        raise ValueError("La contraseña debe contener al menos un carácter especial (!@#$%^&*...).")


def hash_password(password: str, rounds: int = 10) -> str:
    """Hash password using bcrypt after validating complexity."""
    validate_password_complexity(password)
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False
