import threading
from tkinter import messagebox

import customtkinter as ctk

from ..api_client import ApiError
from ..thread_utils import UiTaskQueue


class UserAdminDialog(ctk.CTkToplevel):
    def __init__(self, master_app):
        super().__init__(master_app)
        self.master_app = master_app
        self._ui_tasks = UiTaskQueue()

        self.title("Kelola Pengguna")
        self.geometry("480x560")
        self.minsize(420, 420)
        self.transient(master_app)

        # ---------- Header: DIPAKU DI ATAS ----------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x")
        ctk.CTkLabel(header, text="Persetujuan Pengguna Baru", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(20, 4)
        )
        ctk.CTkLabel(header, text="Akun yang mendaftar menunggu persetujuan Anda di sini", text_color="gray").pack(
            pady=(0, 10)
        )

        # ---------- Footer: DIPAKU DI BAWAH ----------
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x")
        self.status_label = ctk.CTkLabel(footer, text="", text_color="gray", wraplength=420)
        self.status_label.pack(pady=(4, 0))
        ctk.CTkButton(
            footer, text="Tutup", width=140, fg_color="transparent", border_width=1, command=self.destroy
        ).pack(pady=(6, 16))

        # ---------- Tengah: daftar pengguna, mengisi sisa ruang ----------
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(side="top", fill="both", expand=True, padx=20, pady=(6, 10))

        self.after(50, self._poll_ui_tasks)
        self._load_pending()

        # PENTING: grab_set() di akhir, setelah semua widget dibuat & window
        # sempat viewable -- lihat catatan yang sama di upload_dialog.py.
        self.update_idletasks()
        try:
            self.grab_set()
        except Exception:
            pass

    def _poll_ui_tasks(self):
        self._ui_tasks.drain()
        if self.winfo_exists():
            self.after(50, self._poll_ui_tasks)

    def _load_pending(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.list_frame, text="Memuat...", text_color="gray").pack(pady=20)
        threading.Thread(target=self._fetch_pending, daemon=True).start()

    def _fetch_pending(self):
        try:
            users = self.master_app.api.list_pending_users()
            self._ui_tasks.push(lambda: self._render_pending(users))
        except ApiError as e:
            msg = e.message
            self._ui_tasks.push(lambda: self._show_status(msg, error=True))
        except Exception:
            self._ui_tasks.push(lambda: self._show_status("Gagal memuat daftar pengguna.", error=True))

    def _render_pending(self, users):
        if not self.winfo_exists():
            return
        for w in self.list_frame.winfo_children():
            w.destroy()

        if not users:
            ctk.CTkLabel(
                self.list_frame, text="Tidak ada pendaftar yang menunggu saat ini.", text_color="gray"
            ).pack(pady=30)
            return

        for user in users:
            self._build_user_row(user)

    def _build_user_row(self, user):
        row = ctk.CTkFrame(self.list_frame, corner_radius=8)
        row.pack(fill="x", pady=4, padx=2)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=(12, 6), pady=10)
        ctk.CTkLabel(info, text=user["username"], font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(
            fill="x"
        )
        if user.get("nama_lengkap"):
            ctk.CTkLabel(
                info, text=user["nama_lengkap"], text_color="gray", font=ctk.CTkFont(size=11), anchor="w"
            ).pack(fill="x")

        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.pack(side="right", padx=(6, 12), pady=10)
        ctk.CTkButton(
            btns,
            text="Setujui",
            width=80,
            fg_color="#22c55e",
            hover_color="#16a34a",
            command=lambda uid=user["id"]: self._approve(uid),
        ).grid(row=0, column=0, padx=3)
        ctk.CTkButton(
            btns,
            text="Tolak",
            width=70,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=lambda uid=user["id"], uname=user["username"]: self._confirm_reject(uid, uname),
        ).grid(row=0, column=1, padx=3)

    def _approve(self, user_id):
        threading.Thread(target=self._do_approve, args=(user_id,), daemon=True).start()

    def _do_approve(self, user_id):
        try:
            self.master_app.api.approve_user(user_id)
            self._ui_tasks.push(lambda: self._on_action_done("Pengguna disetujui."))
        except ApiError as e:
            msg = e.message
            self._ui_tasks.push(lambda: self._show_status(msg, error=True))
        except Exception:
            self._ui_tasks.push(lambda: self._show_status("Gagal menyetujui pengguna.", error=True))

    def _confirm_reject(self, user_id, username):
        if messagebox.askyesno("Tolak Pendaftar", f'Yakin ingin menolak "{username}"? Akun ini akan dihapus.'):
            threading.Thread(target=self._do_reject, args=(user_id,), daemon=True).start()

    def _do_reject(self, user_id):
        try:
            self.master_app.api.reject_user(user_id)
            self._ui_tasks.push(lambda: self._on_action_done("Pendaftar ditolak dan dihapus."))
        except ApiError as e:
            msg = e.message
            self._ui_tasks.push(lambda: self._show_status(msg, error=True))
        except Exception:
            self._ui_tasks.push(lambda: self._show_status("Gagal menolak pendaftar.", error=True))

    def _on_action_done(self, message):
        if not self.winfo_exists():
            return
        self._show_status(message, error=False)
        self._load_pending()

    def _show_status(self, message, error: bool):
        if not self.winfo_exists():
            return
        self.status_label.configure(text=message, text_color="#e74c3c" if error else "#22c55e")
