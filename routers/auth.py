### routers/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import select
from database.models import User
from database.db import engine
from core.security import hash_password, verify_password, create_access_token
from sqlalchemy.exc import IntegrityError
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest):
    logger.info(f"Signup attempt for email: {payload.email}")
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    from sqlmodel import Session

    with Session(engine) as session:
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"User created: {user}")
        except IntegrityError:
            logger.warning(f"Signup failed: Email already registered - {payload.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
    logger.info(f"Signup successful, token issued for: {user.email}")
    return {"access_token": access_token}


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    logger.info(f"Login attempt for email: {payload.email}")
    from sqlmodel import Session

    with Session(engine) as session:
        statement = select(User).where(User.email == payload.email)
        user = session.exec(statement).first()
        if not user or not verify_password(payload.password, user.password_hash):
            logger.warning(f"Login failed for email: {payload.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    logger.info(f"Login successful, token issued for: {user.email}")
    return {"access_token": access_token}
