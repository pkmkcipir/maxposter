from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/folders", tags=["folders"])


@router.post("", response_model=schemas.FolderResponse)
def create_folder(
    data: schemas.FolderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nama folder tidak boleh kosong")

    existing = db.query(models.Folder).filter(models.Folder.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Folder dengan nama ini sudah ada")

    folder = models.Folder(name=name, created_by_id=current_user.id)
    db.add(folder)
    db.commit()
    db.refresh(folder)

    result = schemas.FolderResponse.model_validate(folder)
    result.poster_count = 0
    return result


@router.get("", response_model=List[schemas.FolderResponse])
def list_folders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    rows = (
        db.query(models.Folder, func.count(models.Poster.id))
        .outerjoin(models.Poster, models.Poster.folder_id == models.Folder.id)
        .group_by(models.Folder.id)
        .order_by(models.Folder.name)
        .all()
    )
    results = []
    for folder, count in rows:
        r = schemas.FolderResponse.model_validate(folder)
        r.poster_count = count
        results.append(r)
    return results
