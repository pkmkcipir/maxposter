"""
Konfigurasi Maxposter Client.

Data pengguna (pengaturan & cache thumbnail) disimpan di %LOCALAPPDATA%\\Maxposter
(bukan di folder instalasi Program Files), karena folder Program Files butuh hak
admin untuk ditulis. Ini pola standar aplikasi Windows.
"""
import json
import os
from pathlib import Path

APP_NAME = "Maxposter"

DEFAULT_SETTINGS = {
    "server_url": "http://127.0.0.1:8000",
    "token": "",
    "username": "",
}


def get_app_data_dir() -> Path:
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
        base = Path(local_appdata) / APP_NAME
    else:
        base = Path.home() / f".{APP_NAME.lower()}"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_cache_dir() -> Path:
    cache_dir = get_app_data_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _settings_path() -> Path:
    return get_app_data_dir() / "settings.json"


def load_settings() -> dict:
    path = _settings_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**DEFAULT_SETTINGS, **data}
        except (OSError, json.JSONDecodeError):
            return dict(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    path = _settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
