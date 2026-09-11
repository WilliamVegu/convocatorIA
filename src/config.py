"""Application configuration module."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Central configuration for ATS Core MVP."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///ats_demo.db")
    APISPERU_TOKEN: str = os.getenv("APISPERU_TOKEN", "")
    APISPERU_BASE_URL: str = os.getenv(
        "APISPERU_BASE_URL", "https://dniruc.apisperu.com/api/v1/dni"
    )
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tcs-ats-secret-key-change-in-production-2026")
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

    # Security policies
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Financial default factor
    DEFAULT_FACTOR_CTC: float = 1.56
    NET_TO_GROSS_FACTOR: float = 0.79

    @classmethod
    def is_sqlite(cls) -> bool:
        return cls.DATABASE_URL.startswith("sqlite")


config = Config()
