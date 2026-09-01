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
    sudah ada. Jadi kalau server ini pernah dijalankan sebelum suatu fitur
    ditambahkan, kolom barunya perlu ditambahkan manual di sini supaya
    database lama tetap kompatibel tanpa perlu dihapus/reset."""
    with engine.connect() as conn:
        # --- Migrasi folder_id di posters ---
        cols = conn.execute(text("PRAGMA table_info(posters)")).fetchall()
        col_names = [c[1] for c in cols]
        if "folder_id" not in col_names:
            conn.execute(text("ALTER TABLE posters ADD COLUMN folder_id INTEGER"))
            conn.commit()

        # --- Migrasi is_admin & is_approved di users (fitur persetujuan admin) ---
        user_cols = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        user_col_names = [c[1] for c in user_cols]
        is_new_migration = "is_admin" not in user_col_names

        if is_new_migration:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
        if "is_approved" not in user_col_names:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_approved BOOLEAN NOT NULL DEFAULT 0"))
        conn.commit()

        if is_new_migration:
            # Database lama: semua akun yang SUDAH ADA otomatis dianggap
            # disetujui (mereka sudah dipakai sebelum fitur ini ada, jangan
            # sampai tiba-tiba terkunci keluar), dan akun dengan id terkecil
            # (paling pertama daftar) otomatis dijadikan admin supaya ada
            # yang bisa menyetujui pendaftar baru berikutnya.
            conn.execute(text("UPDATE users SET is_approved = 1"))
            first_user = conn.execute(text("SELECT id FROM users ORDER BY id ASC LIMIT 1")).fetchone()
            if first_user:
                conn.execute(text("UPDATE users SET is_admin = 1 WHERE id = :id"), {"id": first_user[0]})
            conn.commit()
