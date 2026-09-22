from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.jwt import create_token
from auth.security import get_current_user
from auth.users import verify_login

router = APIRouter()


class LoginBody(BaseModel):
    email: str
    password: str


class MeBody(BaseModel):
    email: str


@router.post("/login")
def login(data: LoginBody):
    user = verify_login(data.email, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": user["email"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user["email"],
        "role": user["role"],
    }


@router.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return {"email": user["sub"], "role": user["role"]}