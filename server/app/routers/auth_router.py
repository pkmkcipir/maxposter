from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth, config
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.RegisterResponse)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if config.REGISTER_CODE and (data.register_code or "") != config.REGISTER_CODE:
        raise HTTPException(status_code=403, detail="Kode registrasi salah, hubungi admin")

    existing = db.query(models.User).filter(models.User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah digunakan")

    # Akun PERTAMA di server ini otomatis jadi admin & langsung aktif --
    # supaya selalu ada seseorang yang bisa menyetujui pendaftar berikutnya.
    is_first_user = db.query(models.User).count() == 0

    user = models.User(
        username=data.username,
        password_hash=auth.hash_password(data.password),
        nama_lengkap=data.nama_lengkap,
        is_admin=is_first_user,
        is_approved=is_first_user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if is_first_user:
        token = auth.create_access_token(user.username)
        return schemas.RegisterResponse(
            status="approved",
            message="Registrasi berhasil sebagai admin pertama server ini.",
            username=user.username,
            access_token=token,
            is_admin=True,
        )

    return schemas.RegisterResponse(
        status="pending",
        message="Registrasi berhasil. Akun Anda menunggu persetujuan admin sebelum bisa login.",
        username=user.username,
        access_token=None,
        is_admin=False,
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not auth.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah")

    if not user.is_approved:
        raise HTTPException(
            status_code=403,
            detail="Akun Anda menunggu persetujuan admin. Hubungi admin untuk mengaktifkan akun.",
        )

    token = auth.create_access_token(user.username)
    return schemas.TokenResponse(access_token=token, username=user.username, is_admin=user.is_admin)


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.get("/pending", response_model=List[schemas.PendingUserResponse])
def list_pending_users(
    db: Session = Depends(get_db), admin: models.User = Depends(auth.get_current_admin)
):
    return (
        db.query(models.User)
        .filter(models.User.is_approved == False)  # noqa: E712
        .order_by(models.User.created_at)
        .all()
    )


@router.post("/approve/{user_id}", response_model=schemas.UserResponse)
def approve_user(
    user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_current_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    user.is_approved = True
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def remove_user(
    user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_current_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Tidak bisa menghapus akun sendiri")
    if user.is_admin:
        other_admins = (
            db.query(models.User)
            .filter(models.User.is_admin == True, models.User.id != user.id)  # noqa: E712
            .count()
        )
        if other_admins == 0:
            raise HTTPException(status_code=400, detail="Tidak bisa menghapus admin terakhir")
    db.delete(user)
    db.commit()
    return {"ok": True}
