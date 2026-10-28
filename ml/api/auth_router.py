from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..persistence import service as persistence_service
from ..persistence.db import AsyncSessionLocal
from ..persistence.models import User
from argon2 import PasswordHasher
import os
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

ph = PasswordHasher()
signer = TimestampSigner(os.getenv("SECRET_KEY", "change_me_secret"))

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def set_auth_cookie(response: Response, user_id: int):
    token = signer.sign(str(user_id)).decode()
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=False,  # set to True in production with HTTPS
        samesite="lax",
        path="/",
    )

def clear_auth_cookie(response: Response):
    response.delete_cookie(key="session", path="/")

async def get_current_user(request: Request) -> User:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user_id = int(signer.unsign(token, max_age=86400).decode())
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

@router.post("/register")
async def register(payload: RegisterRequest, response: Response):
    async with AsyncSessionLocal() as session:
        # check duplicate email
        result = await session.execute(select(User).where(User.email == payload.email.lower()))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = ph.hash(payload.password)
        user = User(
            name=payload.name.strip(),
            email=payload.email.lower(),
            password_hash=hashed,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        set_auth_cookie(response, user.id)
        return {"id": user.id, "name": user.name, "email": user.email}

@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == payload.email.lower()))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        try:
            ph.verify(user.password_hash, payload.password)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        set_auth_cookie(response, user.id)
        return {"id": user.id, "name": user.name, "email": user.email}

@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    clear_auth_cookie(response)
    return {"detail": "Logged out"}

@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email}
