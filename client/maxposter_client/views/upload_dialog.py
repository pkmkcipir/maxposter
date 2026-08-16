import os
import threading
from tkinter import filedialog

import customtkinter as ctk

from ..thread_utils import UiTaskQueue

ALLOWED_EXT = (".jpg", ".jpeg", ".png")


class UploadDialog(ctk.CTkToplevel):
    def __init__(self, master_app, on_done):
        super().__init__(master_app)
        self.master_app = master_app
        self.on_done = on_done
        self._ui_tasks = UiTaskQueue()

        self.title("Unggah Poster")
        self.geometry("480x440")
        self.resizable(False, False)
        self.transient(master_app)
        self.grab_set()

        self.files = []

        ctk.CTkLabel(self, text="Unggah Poster Baru", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Format didukung: JPG, JPEG, PNG", text_color="gray").pack()
        ctk.CTkLabel(
            self,
            text="Landscape/potrait terdeteksi otomatis sesuai ukuran gambar",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).pack(pady=(0, 10))

        ctk.CTkButton(self, text="Pilih File...", command=self._pick_files).pack(pady=4)

        self.file_list_frame = ctk.CTkScrollableFrame(self, height=140)
        self.file_list_frame.pack(fill="both", expand=True, padx=20, pady=(6, 10))

        ctk.CTkLabel(self, text="Tag (opsional, pisahkan dengan koma)").pack(anchor="w", padx=20)
        self.tags_entry = ctk.CTkEntry(self, placeholder_text="contoh: promo, ramadhan, event")
        self.tags_entry.pack(fill="x", padx=20, pady=(2, 10))

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack()

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(6, 16))
        self.upload_btn = ctk.CTkButton(btn_row, text="Unggah", width=140, command=self._start_upload)
        self.upload_btn.grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btn_row, text="Batal", width=100, fg_color="transparent", border_width=1, command=self.destroy
        ).grid(row=0, column=1, padx=6)

        self.after(50, self._poll_ui_tasks)

    def _poll_ui_tasks(self):
        self._ui_tasks.drain()
        if self.winfo_exists():
            self.after(50, self._poll_ui_tasks)

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Pilih poster",
            filetypes=[("Gambar", "*.jpg *.jpeg *.png"), ("Semua file", "*.*")],
        )
        if not paths:
            return
        valid = [p for p in paths if p.lower().endswith(ALLOWED_EXT)]
        skipped = len(paths) - len(valid)
        self.files = valid

        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        for p in self.files:
            ctk.CTkLabel(self.file_list_frame, text=os.path.basename(p), anchor="w").pack(fill="x", padx=6, pady=2)

        if skipped:
            self.status_label.configure(
                text=f"{len(self.files)} file siap, {skipped} dilewati (format tidak didukung)",
                text_color="#e67e22",
            )
        else:
            self.status_label.configure(text=f"{len(self.files)} file siap diunggah", text_color="gray")

    def _start_upload(self):
        if not self.files:
            self.status_label.configure(text="Pilih minimal satu file terlebih dahulu", text_color="#e74c3c")
            return
        self.upload_btn.configure(state="disabled", text="Mengunggah...")
        tags = self.tags_entry.get().strip()
        threading.Thread(target=self._do_upload, args=(list(self.files), tags), daemon=True).start()

    def _do_upload(self, files, tags):
        success, failed = 0, 0
        total = len(files)
        for path in files:
            try:
                self.master_app.api.upload_poster(path, tags)
                success += 1
            except Exception:
                failed += 1
            done = success + failed
            self._ui_tasks.push(lambda d=done, t=total: self._update_progress(d, t))
        self._ui_tasks.push(lambda: self._finish(success, failed))

    def _update_progress(self, done, total):
        if self.winfo_exists():
            self.status_label.configure(text=f"Mengunggah... {done}/{total} selesai", text_color="gray")

    def _finish(self, success, failed):
        if not self.winfo_exists():
            return
        self.upload_btn.configure(state="normal", text="Unggah")
        if failed == 0:
            self.status_label.configure(text=f"Berhasil mengunggah {success} poster", text_color="#22c55e")
        else:
            self.status_label.configure(text=f"{success} berhasil, {failed} gagal diunggah", text_color="#e74c3c")
        self.on_done()
        self.after(1200, self._safe_destroy)

    def _safe_destroy(self):
        if self.winfo_exists():
            self.destroy()
