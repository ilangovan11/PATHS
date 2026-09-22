from datetime import datetime, timedelta, timezone

from jose import jwt

from core.config import settings

SECRET = settings.JWT_SECRET
ALGO = settings.JWT_ALGORITHM
EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES


def create_token(data: dict) -> str:
    payload = dict(data)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=[ALGO])