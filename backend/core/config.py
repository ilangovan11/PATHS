"""Application configuration, resolved from environment variables.

Values are read from a .env file at the repository root (if present) and then
from the process environment. No real secrets are stored in the repository.
"""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    APP_NAME = os.getenv("APP_NAME", "PATHS")
    APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
    ENV = os.getenv("ENV", "development")

    # JWT
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    _jwt_secret = os.getenv("JWT_SECRET")
    if _jwt_secret and _jwt_secret != "change-me":
        JWT_SECRET = _jwt_secret
    else:
        # Development fallback: ephemeral secret so the app always starts
        # without a committed secret. Tokens do not survive a restart.
        JWT_SECRET = secrets.token_hex(32)

    # Storage paths. Model artifacts are a tracked product; runtime DB is not.
    MODEL_STORE_DIR = Path(os.getenv("MODEL_STORE_DIR", PROJECT_ROOT / "backend" / "model_store"))
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(PROJECT_ROOT / 'backend' / 'paths.db').as_posix()}",
    )

    # Default accounts created on a fresh database (development/demo only).
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@paths.io")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    VIEWER_EMAIL = os.getenv("VIEWER_EMAIL", "viewer@paths.io")
    VIEWER_PASSWORD = os.getenv("VIEWER_PASSWORD", "viewer123")

    BACKEND_DATA_PATH = PROJECT_ROOT / "backend" / "data" / "raw" / "student_data.csv"


settings = Settings()