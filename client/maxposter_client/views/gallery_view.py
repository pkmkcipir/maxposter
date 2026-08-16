import io
import threading
from concurrent.futures import ThreadPoolExecutor

import customtkinter as ctk
from PIL import Image

from ..api_client import ApiError
from ..thread_utils import UiTaskQueue

CARD_WIDTH = 200
CARD_HEIGHT = 260
THUMB_SIZE = (176, 176)


class PosterCard(ctk.CTkFrame):
    def __init__(self, master, poster, on_click):
        super().__init__(master, width=CARD_WIDTH, height=CARD_HEIGHT, corner_radius=10)
        self.poster = poster
        self.pack_propagate(False)

        self.image_label = ctk.CTkLabel(self, text="", width=THUMB_SIZE[0], height=THUMB_SIZE[1])
        self.image_label.pack(pady=(10, 6))

        name = poster["original_filename"]
        if len(name) > 22:
            name = name[:19] + "..."
        name_label = ctk.CTkLabel(self, text=name, font=ctk.CTkFont(size=12))
        name_label.pack()

        is_landscape = poster["category"] == "landscape"
        badge_color = "#3b82f6" if is_landscape else "#a855f7"
        badge_text = "Landscape" if is_landscape else "Potrait"
        badge = ctk.CTkLabel(
            self,
            text=badge_text,
            font=ctk.CTkFont(size=10),
            text_color="white",
            fg_color=badge_color,
            corner_radius=6,
            width=70,
            height=18,
        )
        badge.pack(pady=(4, 0))

        for widget in (self, self.image_label, name_label, badge):
            widget.bind("<Button-1>", lambda e: on_click(poster))
            widget.configure(cursor="hand2")

    def set_image(self, ctk_image):
        self.image_label.configure(image=ctk_image, text="")
        self.image_label.image = ctk_image

    def set_placeholder_error(self):
        self.image_label.configure(text="Gagal memuat", image=None)


class GalleryView(ctk.CTkFrame):
    def __init__(self, master, on_logout):
        super().__init__(master, fg_color="transparent")
        self.master_app = master
        self.on_logout = on_logout

        self.page = 1
        self.page_size = 20
        self.category = "all"
        self.search_text = ""
        self.total_pages = 1
        self._search_after_id = None
        self._load_token = 0
        self._closed = False

        self.executor = ThreadPoolExecutor(max_workers=6)
        self._ui_tasks = UiTaskQueue()

        self._build_top_bar()
        self._build_grid_area()
        self._build_bottom_bar()

        self.after(50, self._poll_ui_tasks)
        self._load_posters()

    def destroy(self):
        self._closed = True
        super().destroy()

    # ---------- BUILD UI ----------

    def _build_top_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(bar, text="Maxposter", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")

        username = self.master_app.settings.get("username", "")
        ctk.CTkLabel(bar, text=f"Halo, {username}", text_color="gray").pack(side="left", padx=(16, 0))

        ctk.CTkButton(
            bar, text="Keluar", width=80, fg_color="transparent", border_width=1, command=self._logout
        ).pack(side="right")

        ctk.CTkButton(bar, text="+ Unggah Poster", width=140, command=self._open_upload_dialog).pack(
            side="right", padx=(0, 10)
        )

        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(filter_bar, placeholder_text="Cari nama poster atau tag...", width=280)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self._on_search_typed)

        self.category_menu = ctk.CTkOptionMenu(
            filter_bar, values=["Semua", "Landscape", "Potrait"], width=130, command=self._on_category_change
        )
        self.category_menu.pack(side="left", padx=10)

        ctk.CTkLabel(filter_bar, text="Tampilkan:").pack(side="left", padx=(10, 4))
        self.page_size_menu = ctk.CTkOptionMenu(
            filter_bar, values=["20", "50", "100"], width=80, command=self._on_page_size_change
        )
        self.page_size_menu.set("20")
        self.page_size_menu.pack(side="left")

        self.stats_label = ctk.CTkLabel(filter_bar, text="", text_color="gray")
        self.stats_label.pack(side="right")

    def _build_grid_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=12, pady=4)

        try:
            width = self.master_app.winfo_width() or 1150
        except Exception:
            width = 1150
        self.columns = max(3, min(7, width // (CARD_WIDTH + 24)))

        for i in range(self.columns):
            self.scroll_frame.columnconfigure(i, weight=1)

    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(4, 16))

        self.prev_btn = ctk.CTkButton(bar, text="< Sebelumnya", width=120, command=self._prev_page)
        self.prev_btn.pack(side="left")

        self.page_label = ctk.CTkLabel(bar, text="Halaman 1 / 1")
        self.page_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(bar, text="Berikutnya >", width=120, command=self._next_page)
        self.next_btn.pack(side="right")

    # ---------- THREAD-SAFE UI QUEUE ----------

    def _poll_ui_tasks(self):
        self._ui_tasks.drain()
        if not self._closed and self.winfo_exists():
            self.after(50, self._poll_ui_tasks)

    # ---------- EVENTS ----------

    def _on_search_typed(self, event=None):
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(400, self._apply_search)

    def _apply_search(self):
        self.search_text = self.search_entry.get().strip()
        self.page = 1
        self._load_posters()

    def _on_category_change(self, value):
        mapping = {"Semua": "all", "Landscape": "landscape", "Potrait": "portrait"}
        self.category = mapping.get(value, "all")
        self.page = 1
        self._load_posters()

    def _on_page_size_change(self, value):
        self.page_size = int(value)
        self.page = 1
        self._load_posters()

    def _prev_page(self):
        if self.page > 1:
            self.page -= 1
            self._load_posters()

    def _next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self._load_posters()

    def _logout(self):
        self._closed = True
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.on_logout()

    def _open_upload_dialog(self):
        from .upload_dialog import UploadDialog

        UploadDialog(self.master_app, on_done=self._load_posters)

    # ---------- DATA LOADING ----------

    def _load_posters(self):
        self._load_token += 1
        token = self._load_token

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        loading_label = ctk.CTkLabel(self.scroll_frame, text="Memuat poster...", font=ctk.CTkFont(size=14))
        loading_label.grid(row=0, column=0, columnspan=self.columns, pady=40)

        self.prev_btn.configure(state="disabled")
        self.next_btn.configure(state="disabled")

        threading.Thread(target=self._fetch_posters, args=(token,), daemon=True).start()

    def _fetch_posters(self, token):
        try:
            data = self.master_app.api.list_posters(
                category=self.category, search=self.search_text, page=self.page, page_size=self.page_size
            )
            self._ui_tasks.push(lambda: self._handle_posters_loaded(token, data, None))
        except ApiError as e:
            msg = e.message
            self._ui_tasks.push(lambda: self._handle_posters_loaded(token, None, msg))
        except Exception:
            self._ui_tasks.push(
                lambda: self._handle_posters_loaded(token, None, "Gagal memuat data dari server.")
            )

    def _handle_posters_loaded(self, token, data, error):
        if token != self._load_token:
            return
        if error:
            self._show_load_error(error)
        else:
            self._render_posters(data)

    def _render_posters(self, data):
        items = data["items"]
        self.total_pages = data["total_pages"]
        self.page = data["page"]

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not items:
            empty = ctk.CTkLabel(
                self.scroll_frame, text="Tidak ada poster ditemukan", font=ctk.CTkFont(size=14), text_color="gray"
            )
            empty.grid(row=0, column=0, columnspan=self.columns, pady=60)
        else:
            for idx, poster in enumerate(items):
                row, col = divmod(idx, self.columns)
                card = PosterCard(self.scroll_frame, poster, on_click=self._open_viewer)
                card.grid(row=row, column=col, padx=8, pady=8)
                self.executor.submit(self._load_thumbnail, self._load_token, poster, card)

        self.stats_label.configure(text=f"{data['total']} poster ditemukan")
        self.page_label.configure(text=f"Halaman {self.page} / {self.total_pages}")
        self.prev_btn.configure(state="normal" if self.page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.page < self.total_pages else "disabled")

    def _load_thumbnail(self, token, poster, card):
        poster_id = poster["id"]
        cache = self.master_app.cache
        try:
            mem = cache.get_memory(poster_id)
            if mem is not None:
                self._ui_tasks.push(lambda: self._handle_thumb_ready(token, card, mem, None))
                return

            if cache.has_cached_thumbnail(poster_id):
                raw = cache.read_cached_thumbnail(poster_id)
            else:
                raw = self.master_app.api.get_thumbnail_bytes(poster_id)
                cache.save_thumbnail(poster_id, raw)

            img = Image.open(io.BytesIO(raw))
            img.load()
            img.thumbnail(THUMB_SIZE)
            # PENTING: selalu isi light_image DAN dark_image (walau sama) supaya
            # thumbnail tetap tampil baik di mode terang maupun gelap Windows.
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            cache.set_memory(poster_id, ctk_img)
            self._ui_tasks.push(lambda: self._handle_thumb_ready(token, card, ctk_img, None))
        except Exception:
            self._ui_tasks.push(lambda: self._handle_thumb_ready(token, card, None, "error"))

    def _handle_thumb_ready(self, token, card, ctk_img, error):
        if token != self._load_token or not card.winfo_exists():
            return
        if ctk_img is not None:
            card.set_image(ctk_img)
        else:
            card.set_placeholder_error()

    def _show_load_error(self, message):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        err = ctk.CTkLabel(self.scroll_frame, text=f"Gagal memuat: {message}", text_color="#e74c3c")
        err.grid(row=0, column=0, columnspan=self.columns, pady=40)
        self.prev_btn.configure(state="normal" if self.page > 1 else "disabled")
        self.next_btn.configure(state="normal")

    def _open_viewer(self, poster):
        from .image_viewer import ImageViewer

        ImageViewer(self.master_app, poster, on_deleted=self._load_posters)
