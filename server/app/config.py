"""
Konfigurasi Maxposter Server.

PENTING soal path: saat aplikasi ini dijalankan sebagai .exe hasil PyInstaller,
sys.executable menunjuk ke lokasi file .exe (bukan folder temp ekstraksi),
sehingga data (database & storage poster) selalu tersimpan berdampingan dengan
MaxposterServer.exe dan tidak hilang saat aplikasi ditutup/dibuka lagi.
"""
import os
import sys
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        # Dijalankan sebagai .exe hasil PyInstaller
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _resource_dir() -> Path:
    """Lokasi file BUNDEL aplikasi (statis, bukan data pengguna) -- mis. folder
    web/ untuk antarmuka browser. Saat di-frozen PyInstaller, file semacam ini
    diekstrak ke folder temp (sys._MEIPASS), BEDA dengan BASE_DIR di atas yang
    dipakai untuk data PERSISTEN (database & storage poster) yang harus tetap
    berada di sebelah exe supaya tidak hilang saat aplikasi ditutup-buka."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


BASE_DIR = _base_dir()
WEB_DIR = _resource_dir() / "web"

# Bisa dioverride lewat environment variable jika ingin simpan di lokasi lain
STORAGE_DIR = Path(os.getenv("MAXPOSTER_STORAGE_DIR", str(BASE_DIR / "storage")))
LANDSCAPE_DIR = STORAGE_DIR / "landscape"
PORTRAIT_DIR = STORAGE_DIR / "portrait"
THUMBNAIL_DIR = STORAGE_DIR / "thumbnails"

DB_PATH = Path(os.getenv("MAXPOSTER_DB_PATH", str(BASE_DIR / "maxposter.db")))

# Ganti nilai default ini lewat environment variable MAXPOSTER_SECRET_KEY saat produksi
SECRET_KEY = os.getenv("MAXPOSTER_SECRET_KEY", "maxposter-ganti-kunci-rahasia-ini-saat-produksi")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 14  # token berlaku 14 hari

# Jika diisi, pendaftaran akun baru wajib menyertakan kode ini (dibagikan admin ke staf).
# Kosongkan (default) agar pendaftaran terbuka untuk siapa saja yang tahu alamat server.
REGISTER_CODE = os.getenv("MAXPOSTER_REGISTER_CODE", "")

PORT = int(os.getenv("MAXPOSTER_PORT", "8000"))

THUMBNAIL_MAX_SIZE = (320, 320)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB per poster

for _d in (LANDSCAPE_DIR, PORTRAIT_DIR, THUMBNAIL_DIR):
    _d.mkdir(parents=True, exist_ok=True)
