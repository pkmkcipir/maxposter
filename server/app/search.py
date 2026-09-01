"""
Pencarian poster cepat memakai SQLite FTS5 (full text search) dengan matching prefix
(mis. mengetik "prom" akan menemukan "promo"). Jika FTS5 ternyata tidak tersedia di
build Python/SQLite yang dipakai, sistem otomatis jatuh ke pencarian LIKE biasa
supaya aplikasi tetap berjalan normal.
"""
import re

from sqlalchemy import text

from .database import engine

FTS_ENABLED = False


def setup_fts() -> bool:
    global FTS_ENABLED
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS posters_fts USING fts5("
                "original_filename, tags, content='posters', content_rowid='id')"
            ))
            conn.execute(text(
                "CREATE TRIGGER IF NOT EXISTS posters_ai AFTER INSERT ON posters BEGIN "
                "INSERT INTO posters_fts(rowid, original_filename, tags) "
                "VALUES (new.id, new.original_filename, new.tags); END;"
            ))
            conn.execute(text(
                "CREATE TRIGGER IF NOT EXISTS posters_ad AFTER DELETE ON posters BEGIN "
                "INSERT INTO posters_fts(posters_fts, rowid, original_filename, tags) "
                "VALUES('delete', old.id, old.original_filename, old.tags); END;"
            ))
            conn.execute(text(
                "CREATE TRIGGER IF NOT EXISTS posters_au AFTER UPDATE ON posters BEGIN "
                "INSERT INTO posters_fts(posters_fts, rowid, original_filename, tags) "
                "VALUES('delete', old.id, old.original_filename, old.tags); "
                "INSERT INTO posters_fts(rowid, original_filename, tags) "
                "VALUES (new.id, new.original_filename, new.tags); END;"
            ))
            conn.commit()
        FTS_ENABLED = True
    except Exception:
        FTS_ENABLED = False
    return FTS_ENABLED


def build_fts_query(raw: str) -> str:
    words = re.findall(r"\w+", raw, flags=re.UNICODE)
    if not words:
        return ""
    return " OR ".join(f"{w}*" for w in words)
