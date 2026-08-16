from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth, config
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.TokenResponse)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if config.REGISTER_CODE and (data.register_code or "") != config.REGISTER_CODE:
        raise HTTPException(status_code=403, detail="Kode registrasi salah, hubungi admin")

    existing = db.query(models.User).filter(models.User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah digunakan")

    user = models.User(
        username=data.username,
        password_hash=auth.hash_password(data.password),
        nama_lengkap=data.nama_lengkap,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token(user.username)
    return schemas.TokenResponse(access_token=token, username=user.username)


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not auth.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah")

    token = auth.create_access_token(user.username)
    return schemas.TokenResponse(access_token=token, username=user.username)


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
