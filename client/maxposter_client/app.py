import customtkinter as ctk

from . import config
from .api_client import ApiClient
from .cache_manager import CacheManager
from .views.login_view import LoginView
from .views.gallery_view import GalleryView

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class MaxposterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Maxposter")
        self.geometry("1150x720")
        self.minsize(950, 600)

        self.settings = config.load_settings()
        self.api = ApiClient(
            self.settings.get("server_url", "http://127.0.0.1:8000"),
            self.settings.get("token", ""),
        )
        self.cache = CacheManager()

        self.current_view = None
        self._show_login()

    def _clear_view(self):
        if self.current_view is not None:
            self.current_view.destroy()
            self.current_view = None

    def _show_login(self):
        self._clear_view()
        self.current_view = LoginView(self, on_success=self._on_login_success)
        self.current_view.pack(fill="both", expand=True)

    def _on_login_success(self, token: str, username: str):
        self.settings["token"] = token
        self.settings["username"] = username
        config.save_settings(self.settings)
        self.api.token = token
        # Namespace cache berdasarkan server aktif SEBELUM galeri memakainya,
        # supaya thumbnail tidak pernah tertukar antar server berbeda.
        self.cache.set_server(self.api.base_url)
        self._show_gallery()

    def _show_gallery(self):
        self._clear_view()
        self.current_view = GalleryView(self, on_logout=self._on_logout)
        self.current_view.pack(fill="both", expand=True)

    def _on_logout(self):
        self.settings["token"] = ""
        config.save_settings(self.settings)
        self.api.token = ""
        self._show_login()


def run():
    app = MaxposterApp()
    app.mainloop()
