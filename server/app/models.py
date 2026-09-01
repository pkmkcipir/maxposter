import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nama_lengkap = Column(String(100), nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_approved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    posters = relationship("Poster", back_populates="uploader")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    posters = relationship("Poster", back_populates="folder")


class Poster(Base):
    __tablename__ = "posters"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)            # nama file unik tersimpan di disk
    original_filename = Column(String(255), nullable=False)   # nama file asli saat diunggah
    category = Column(String(10), nullable=False, index=True)  # "landscape" atau "portrait"
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    filesize = Column(Integer, nullable=False)
    tags = Column(String(255), nullable=True, default="")
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    uploader = relationship("User", back_populates="posters")
    folder = relationship("Folder", back_populates="posters")


Index("ix_posters_category_uploaded_at", Poster.category, Poster.uploaded_at)
