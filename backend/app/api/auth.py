from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app import models
from app.schemas.auth import UserCreate, Token
from passlib.context import CryptContext
import jwt
from app.core.config import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def create_access_token(data: dict):
    return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")


@router.post("/register", response_model=Token)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd_context.hash(payload.password)
    u = models.User(email=payload.email, password_hash=hashed)
    db.add(u)
    db.commit()
    db.refresh(u)
    token = create_access_token({"user_id": str(u.id)})
    return {"access_token": token}


@router.post("/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"user_id": str(user.id)})
    return {"access_token": token}
