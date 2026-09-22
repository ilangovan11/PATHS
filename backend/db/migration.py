"""Idempotent, additive schema management.

- Creates missing tables.
- Adds missing columns to existing tables (SQLite ALTER TABLE ADD COLUMN).
- Seeds default development users with bcrypt-hashed passwords.

Existing rows are never deleted or rewritten.
"""

from sqlalchemy import inspect, text

from db.database import Base, engine
from db.models import DecisionLog, User
from core.logging import get_logger

logger = get_logger()

# Paths added in PATHS 2.0; needed only on databases created by v1.0.
_MIGRATIONS = [
    ("decision_logs", "created_at", "VARCHAR"),
    ("decision_logs", "model_version", "VARCHAR"),
    ("decision_logs", "decision_trace", "TEXT"),
]


def _ensure_columns() -> None:
    inspector = inspect(engine)
    existing = {t: {c["name"] for c in inspector.get_columns(t)} for t in inspector.get_table_names()}

    with engine.begin() as conn:
        for table, column, col_type in _MIGRATIONS:
            if table not in existing:
                continue
            if column in existing[table]:
                continue
            conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
            logger.info("DB migration: added %s.%s", table, column)


def seed_users() -> None:
    """Create the two documented demo users if absent (idempotent)."""
    from auth.security import hash_password

    defaults = [
        {"email": "admin@paths.io", "password": "admin123", "role": "admin"},
        {"email": "viewer@paths.io", "password": "viewer123", "role": "viewer"},
    ]

    from db.database import SessionLocal

    db = SessionLocal()
    try:
        for u in defaults:
            exists = db.query(User).filter(User.email == u["email"]).first()
            if exists:
                continue
            db.add(
                User(
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                )
            )
        db.commit()
    finally:
        db.close()


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    seed_users()
    logger.info("Database schema ready (%s)", engine.url)