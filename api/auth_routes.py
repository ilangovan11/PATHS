from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.users import users
from auth.jwt import create_token

router = APIRouter()

class Login(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(data: Login):
    user = users.get(data.email)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": data.email, "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}
