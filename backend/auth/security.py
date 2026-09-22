"""Password hashing and authentication dependencies.

Passwords are stored as bcrypt hashes, never as plaintext. Roles are enforced
via the token-embedded role claim + a DB check for robustness.
"""

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.jwt import decode_token
from db.database import SessionLocal
from db.models import User
from core.logging import get_logger

logger = get_logger()

security = HTTPBearer(auto_error=True)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _load_user(email: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Require a valid JWT; returns a dict with sub (email) and role."""
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        logger.warning("Authentication rejected: invalid/expired/malformed token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = payload.get("sub")
    role = payload.get("role")
    # Verify the user still exists and role matches the stored record.
    user = _load_user(email) if email else None
    if user is None:
        raise HTTPException(status_code=401, detail="Account not found")
    if user.role != role:
        raise HTTPException(status_code=401, detail="Token role mismatch")
    return {"sub": user.email, "role": user.role}


def admin_only(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user