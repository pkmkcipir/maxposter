import threading

import customtkinter as ctk

from .. import config
from ..api_client import ApiError
from ..thread_utils import UiTaskQueue

ERROR_COLOR = "#e74c3c"
SUCCESS_COLOR = "#22c55e"


class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master, fg_color="transparent")
        self.master_app = master
        self.on_success = on_success
        self.mode = "login"  # atau "register"
        self._closed = False
        self._ui_tasks = UiTaskQueue()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, width=420, corner_radius=16)
        container.grid(row=0, column=0)
        container.grid_propagate(False)

        ctk.CTkLabel(container, text="Maxposter", font=ctk.CTkFont(size=28, weight="bold")).pack(
            pady=(36, 4), padx=40
        )
        self.subtitle = ctk.CTkLabel(container, text="Masuk ke akun Anda", text_color="gray")
        self.subtitle.pack(pady=(0, 20))

        self.server_entry = ctk.CTkEntry(container, width=320, placeholder_text="Alamat server (http://IP:8000)")
        self.server_entry.insert(0, self.master_app.settings.get("server_url", "http://127.0.0.1:8000"))
        self.server_entry.pack(pady=6, padx=40)

        self.nama_entry = ctk.CTkEntry(container, width=320, placeholder_text="Nama lengkap (opsional)")

        self.username_entry = ctk.CTkEntry(container, width=320, placeholder_text="Username")
        self.username_entry.pack(pady=6, padx=40)

        self.password_entry = ctk.CTkEntry(container, width=320, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=6, padx=40)

        self.code_entry = ctk.CTkEntry(container, width=320, placeholder_text="Kode registrasi (jika diminta admin)")

        self.error_label = ctk.CTkLabel(container, text="", text_color=ERROR_COLOR, wraplength=320)
        self.error_label.pack(pady=(4, 0))

        self.submit_btn = ctk.CTkButton(container, text="Masuk", width=320, command=self._submit)
        self.submit_btn.pack(pady=(16, 6), padx=40)

        self.toggle_btn = ctk.CTkButton(
            container,
            text="Belum punya akun? Daftar",
            width=320,
            fg_color="transparent",
            text_color=("gray20", "gray80"),
            hover_color=("gray90", "gray25"),
            command=self._toggle_mode,
        )
        self.toggle_btn.pack(pady=(0, 36), padx=40)

        self.username_entry.bind("<Return>", lambda e: self._submit())
        self.password_entry.bind("<Return>", lambda e: self._submit())

        self.after(50, self._poll_ui_tasks)

    def destroy(self):
        self._closed = True
        super().destroy()

    def _poll_ui_tasks(self):
        self._ui_tasks.drain()
        if not self._closed and self.winfo_exists():
            self.after(50, self._poll_ui_tasks)

    def _toggle_mode(self):
        self.error_label.configure(text="", text_color=ERROR_COLOR)
        if self.mode == "login":
            self.mode = "register"
            self.subtitle.configure(text="Buat akun baru")
            self.submit_btn.configure(text="Daftar")
            self.toggle_btn.configure(text="Sudah punya akun? Masuk")
            self.nama_entry.pack(pady=6, padx=40, before=self.username_entry)
            self.code_entry.pack(pady=6, padx=40, after=self.password_entry)
        else:
            self.mode = "login"
            self.subtitle.configure(text="Masuk ke akun Anda")
            self.submit_btn.configure(text="Masuk")
            self.toggle_btn.configure(text="Belum punya akun? Daftar")
            self.nama_entry.pack_forget()
            self.code_entry.pack_forget()

    def _set_loading(self, loading: bool):
        state = "disabled" if loading else "normal"
        default_text = "Daftar" if self.mode == "register" else "Masuk"
        self.submit_btn.configure(state=state, text="Memproses..." if loading else default_text)
        self.toggle_btn.configure(state=state)

    def _submit(self):
        server_url = self.server_entry.get().strip().rstrip("/")
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not server_url or not username or not password:
            self.error_label.configure(text="Mohon lengkapi semua data", text_color=ERROR_COLOR)
            return

        self.master_app.settings["server_url"] = server_url
        config.save_settings(self.master_app.settings)
        self.master_app.api.base_url = server_url

        self.error_label.configure(text="", text_color=ERROR_COLOR)
        self._set_loading(True)

        if self.mode == "login":
            threading.Thread(target=self._do_login, args=(username, password), daemon=True).start()
        else:
            nama = self.nama_entry.get().strip()
            code = self.code_entry.get().strip()
            threading.Thread(target=self._do_register, args=(username, password, nama, code), daemon=True).start()

    def _do_login(self, username, password):
        try:
            result = self.master_app.api.login(username, password)
            self._ui_tasks.push(lambda: self._on_login_success(result))
        except ApiError as e:
            msg = e.message
            self._ui_tasks.push(lambda: self._on_error(msg))
        except Exception:
            self._ui_tasks.push(lambda: self._on_error(
                "Tidak dapat terhubung ke server. Periksa alamat server dan koneksi jaringan."
            ))

    def _do_register(self, username, password, nama, code):
        try:
            result = self.master_app.api.register(username, password, nama, code)
            self._ui_tasks.push(lambda: self._on_register_result(result))
        except ApiError as e:
            msg = e.message
            self._ui_tasks.push(lambda: self._on_error(msg))
        except Exception:
            self._ui_tasks.push(lambda: self._on_error(
                "Tidak dapat terhubung ke server. Periksa alamat server dan koneksi jaringan."
            ))

    def _on_login_success(self, result):
        if self._closed or not self.winfo_exists():
            return
        self._set_loading(False)
        self.on_success(result["access_token"], result["username"], result.get("is_admin", False))

    def _on_register_result(self, result):
        """Registrasi bisa menghasilkan dua kondisi berbeda:
        - "approved": akun pertama di server ini -> langsung jadi admin & bisa masuk.
        - "pending": akun biasa -> harus menunggu admin menyetujui dulu sebelum bisa login,
          jadi TIDAK langsung diarahkan ke galeri, hanya ditampilkan pesan konfirmasi."""
        if self._closed or not self.winfo_exists():
            return
        self._set_loading(False)

        if result.get("access_token"):
            self.on_success(result["access_token"], result["username"], result.get("is_admin", False))
            return

        if self.mode == "register":
            self._toggle_mode()
        self.password_entry.delete(0, "end")
        self.error_label.configure(
            text=result.get("message", "Registrasi berhasil. Menunggu persetujuan admin."),
            text_color=SUCCESS_COLOR,
        )

    def _on_error(self, message):
        if self._closed or not self.winfo_exists():
            return
        self._set_loading(False)
        self.error_label.configure(text=message, text_color=ERROR_COLOR)
