from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from .. import models, schemas, auth, config, image_utils
from ..database import get_db
from ..search import build_fts_query, FTS_ENABLED

router = APIRouter(prefix="/posters", tags=["posters"])


@router.post("/upload", response_model=schemas.PosterResponse)
async def upload_poster(
    file: UploadFile = File(...),
    tags: str = Form(""),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    content = await file.read()

    try:
        filename, category, width, height, filesize = image_utils.save_poster(content, file.filename or "poster.jpg")
    except image_utils.InvalidImageError as e:
        raise HTTPException(status_code=400, detail=str(e))

    poster = models.Poster(
        filename=filename,
        original_filename=file.filename or filename,
        category=category,
        width=width,
        height=height,
        filesize=filesize,
        tags=tags or "",
        uploaded_by_id=current_user.id,
    )
    db.add(poster)
    db.commit()
    db.refresh(poster)

    result = schemas.PosterResponse.model_validate(poster)
    result.uploaded_by = current_user.username
    return result


@router.get("", response_model=schemas.PosterListResponse)
def list_posters(
    category: str = Query("all", pattern="^(all|landscape|portrait)$"),
    search: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Poster)

    if category != "all":
        query = query.filter(models.Poster.category == category)

    search = search.strip()
    if search:
        if FTS_ENABLED:
            fts_query = build_fts_query(search)
            if fts_query:
                rows = db.execute(
                    text("SELECT rowid FROM posters_fts WHERE posters_fts MATCH :q"),
                    {"q": fts_query},
                )
                ids = [row[0] for row in rows]
                query = query.filter(models.Poster.id.in_(ids))
        else:
            like = f"%{search}%"
            query = query.filter(
                or_(models.Poster.original_filename.ilike(like), models.Poster.tags.ilike(like))
            )

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)

    items = (
        query.order_by(models.Poster.uploaded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for p in items:
        r = schemas.PosterResponse.model_validate(p)
        r.uploaded_by = p.uploader.username if p.uploader else None
        results.append(r)

    return schemas.PosterListResponse(
        items=results, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/stats", response_model=schemas.StatsResponse)
def stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    total = db.query(models.Poster).count()
    landscape = db.query(models.Poster).filter(models.Poster.category == "landscape").count()
    portrait = db.query(models.Poster).filter(models.Poster.category == "portrait").count()
    return schemas.StatsResponse(total=total, landscape=landscape, portrait=portrait)


@router.get("/{poster_id}/thumbnail")
def get_thumbnail(
    poster_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    poster = db.query(models.Poster).filter(models.Poster.id == poster_id).first()
    if not poster:
        raise HTTPException(status_code=404, detail="Poster tidak ditemukan")
    path = config.THUMBNAIL_DIR / poster.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail tidak ditemukan")
    return FileResponse(path)


@router.get("/{poster_id}/file")
def get_file(
    poster_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    poster = db.query(models.Poster).filter(models.Poster.id == poster_id).first()
    if not poster:
        raise HTTPException(status_code=404, detail="Poster tidak ditemukan")
    target_dir = config.LANDSCAPE_DIR if poster.category == "landscape" else config.PORTRAIT_DIR
    path = target_dir / poster.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    return FileResponse(path, filename=poster.original_filename)


@router.delete("/{poster_id}")
def delete_poster(
    poster_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    poster = db.query(models.Poster).filter(models.Poster.id == poster_id).first()
    if not poster:
        raise HTTPException(status_code=404, detail="Poster tidak ditemukan")
    image_utils.delete_poster_files(poster.filename, poster.category)
    db.delete(poster)
    db.commit()
    return {"ok": True}
