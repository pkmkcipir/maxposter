from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DB_PATH

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False, "timeout": 15},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """WAL mode + busy_timeout supaya beberapa PC yang akses bersamaan
    tidak langsung gagal dengan error 'database is locked'."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=15000")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations() -> None:
    """Migrasi ringan untuk database lama. Base.metadata.create_all() hanya
    membuat tabel yang belum ada, TIDAK menambah kolom baru ke tabel yang
    sudah ada. Jadi kalau server ini pernah dijalankan sebelum fitur folder
    ditambahkan, kolom folder_id perlu ditambahkan manual di sini supaya
    database lama tetap kompatibel tanpa perlu dihapus/reset."""
    with engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(posters)")).fetchall()
        col_names = [c[1] for c in cols]
        if "folder_id" not in col_names:
            conn.execute(text("ALTER TABLE posters ADD COLUMN folder_id INTEGER"))
            conn.commit()
