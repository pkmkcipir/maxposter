import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from . import config


class InvalidImageError(Exception):
    pass


def detect_category(width: int, height: int) -> str:
    """Lebar >= tinggi dianggap landscape, selain itu portrait."""
    return "landscape" if width >= height else "portrait"


def unique_filename(original_filename: str) -> str:
    ext = Path(original_filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        ext = ".jpg"
    return f"{uuid.uuid4().hex}{ext}"


def save_poster(file_bytes: bytes, original_filename: str):
    """Validasi gambar, simpan file asli ke folder sesuai kategori (landscape/portrait),
    lalu buat thumbnail untuk mempercepat tampilan galeri.
    Mengembalikan tuple (filename, category, width, height, filesize).
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise InvalidImageError("Format file harus JPG, JPEG, atau PNG")

    if len(file_bytes) > config.MAX_UPLOAD_SIZE_BYTES:
        raise InvalidImageError("Ukuran file melebihi batas maksimal 25MB")

    try:
        img = Image.open(BytesIO(file_bytes))
        img.load()  # memaksa decode penuh, akan gagal jika file benar-benar rusak
    except (UnidentifiedImageError, OSError):
        raise InvalidImageError("File bukan gambar yang valid atau rusak")

    width, height = img.size
    category = detect_category(width, height)
    filename = unique_filename(original_filename)

    target_dir = config.LANDSCAPE_DIR if category == "landscape" else config.PORTRAIT_DIR
    target_path = target_dir / filename
    with open(target_path, "wb") as f:
        f.write(file_bytes)

    # Buat thumbnail (dipakai agar halaman galeri tidak berat saat memuat banyak poster)
    thumb = img.copy()
    thumb.thumbnail(config.THUMBNAIL_MAX_SIZE)
    thumb_path = config.THUMBNAIL_DIR / filename
    if ext in (".jpg", ".jpeg"):
        if thumb.mode not in ("RGB", "L"):
            thumb = thumb.convert("RGB")
        thumb.save(thumb_path, "JPEG", quality=85)
    else:
        thumb.save(thumb_path, "PNG")

    filesize = len(file_bytes)
    return filename, category, width, height, filesize


def delete_poster_files(filename: str, category: str) -> None:
    target_dir = config.LANDSCAPE_DIR if category == "landscape" else config.PORTRAIT_DIR
    for p in (target_dir / filename, config.THUMBNAIL_DIR / filename):
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
