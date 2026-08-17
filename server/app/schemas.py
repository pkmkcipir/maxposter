import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    nama_lengkap: Optional[str] = None
    register_code: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    nama_lengkap: Optional[str] = None

    class Config:
        from_attributes = True


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FolderResponse(BaseModel):
    id: int
    name: str
    created_at: datetime.datetime
    poster_count: int = 0

    class Config:
        from_attributes = True


class PosterResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    category: str
    width: int
    height: int
    filesize: int
    tags: Optional[str] = ""
    folder_id: Optional[int] = None
    folder_name: Optional[str] = None
    uploaded_at: datetime.datetime
    uploaded_by: Optional[str] = None

    class Config:
        from_attributes = True


class PosterListResponse(BaseModel):
    items: List[PosterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatsResponse(BaseModel):
    total: int
    landscape: int
    portrait: int
