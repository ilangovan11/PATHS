"""Login provider backed by the database ``users`` table.

Replaces the v1.0 hard-coded plaintext credentials dict.
"""

from auth.security import verify_password
from db.database import SessionLocal
from db.models import User


def verify_login(email: str, password: str) -> dict | None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
    finally:
        db.close()

    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return {"email": user.email, "role": user.role}