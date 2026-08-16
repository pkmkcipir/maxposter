import hashlib
from pathlib import Path

from . import config


class CacheManager:
    """
    Dua lapis cache supaya halaman awal galeri tidak berat:
    1. Disk cache -> thumbnail tersimpan di %LOCALAPPDATA%\\Maxposter\\cache,
       jadi saat aplikasi dibuka ulang tidak perlu download ulang dari server.
    2. Memory cache (LRU sederhana) -> objek CTkImage yang sudah pernah dibuat
       disimpan di RAM selama aplikasi berjalan, supaya bolak-balik halaman
       (next/back) terasa instan tanpa decode ulang gambar.

    PENTING: cache dinamespace per alamat server (lewat set_server()). ID poster
    hanyalah angka urut di database masing-masing server, jadi tanpa namespace,
    pindah/reset server dengan ID yang kebetulan sama bisa membuat thumbnail
    poster yang SALAH ikut tertampil dari cache lama.
    """

    def __init__(self, memory_limit: int = 300):
        self._cache_root = config.get_cache_dir()
        self._current_server = None
        self.cache_dir = self._cache_root
        self._memory_cache = {}
        self._memory_order = []
        self._memory_limit = memory_limit

    def set_server(self, server_url: str) -> None:
        """Panggil setiap kali server aktif berubah (mis. tepat setelah login
        berhasil) agar cache tidak pernah tercampur antar server berbeda."""
        server_url = (server_url or "").strip().lower()
        if server_url == self._current_server:
            return
        self._current_server = server_url
        server_hash = hashlib.sha256(server_url.encode("utf-8")).hexdigest()[:16]
        self.cache_dir = self._cache_root / server_hash
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Cache memori juga direset karena bisa berisi CTkImage dari server lama
        self._memory_cache.clear()
        self._memory_order.clear()

    def get_thumbnail_path(self, poster_id: int) -> Path:
        return self.cache_dir / f"poster_{poster_id}.jpg"

    def has_cached_thumbnail(self, poster_id: int) -> bool:
        return self.get_thumbnail_path(poster_id).exists()

    def read_cached_thumbnail(self, poster_id: int) -> bytes:
        with open(self.get_thumbnail_path(poster_id), "rb") as f:
            return f.read()

    def save_thumbnail(self, poster_id: int, data: bytes) -> None:
        try:
            with open(self.get_thumbnail_path(poster_id), "wb") as f:
                f.write(data)
        except OSError:
            pass

    def invalidate(self, poster_id: int) -> None:
        try:
            self.get_thumbnail_path(poster_id).unlink(missing_ok=True)
        except OSError:
            pass
        self._memory_cache.pop(poster_id, None)

    def get_memory(self, key):
        return self._memory_cache.get(key)

    def set_memory(self, key, value) -> None:
        if key not in self._memory_cache and len(self._memory_order) >= self._memory_limit:
            oldest = self._memory_order.pop(0)
            self._memory_cache.pop(oldest, None)
        if key not in self._memory_cache:
            self._memory_order.append(key)
        self._memory_cache[key] = value
