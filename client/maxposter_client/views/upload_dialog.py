import os
import threading
from tkinter import filedialog

import customtkinter as ctk

from ..api_client import ApiError
from ..thread_utils import UiTaskQueue

ALLOWED_EXT = (".jpg", ".jpeg", ".png")
NO_FOLDER_LABEL = "Tanpa Folder"
CREATE_FOLDER_LABEL = "+ Buat Folder Baru..."


class UploadDialog(ctk.CTkToplevel):
    def __init__(self, master_app, on_done):
        super().__init__(master_app)
        self.master_app = master_app
        self.on_done = on_done
        self._ui_tasks = UiTaskQueue()

        self.title("Unggah Poster")
        self.geometry("480x600")
        self.minsize(440, 500)
        self.resizable(False, False)
        self.transient(master_app)

        self.files = []
        self.folder_map = {}  # nama folder -> id
        self.selected_folder_id = None

        # ---------- Header: DIPAKU DI ATAS (side="top") ----------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x")

        ctk.CTkLabel(header, text="Unggah Poster Baru", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(header, text="Format didukung: JPG, JPEG, PNG", text_color="gray").pack()
        ctk.CTkLabel(
            header,
            text="Landscape/potrait terdeteksi otomatis sesuai ukuran gambar",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).pack(pady=(0, 10))
        ctk.CTkButton(header, text="Pilih File...", command=self._pick_files).pack(pady=(0, 10))

        # ---------- Footer: DIPAKU DI BAWAH (side="bottom") ----------
        # PENTING: dipaketkan dengan side="bottom" SEBELUM area file (yang expand=True)
        # supaya tombol Unggah/Batal selalu punya jatah ruang dan tidak pernah
        # terdorong keluar layar walau daftar file atau isi lain bertambah panjang.
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x")

        ctk.CTkLabel(footer, text="Folder tujuan (opsional)").pack(anchor="w", padx=20, pady=(10, 0))
        self.folder_menu = ctk.CTkOptionMenu(footer, values=[NO_FOLDER_LABEL], command=self._on_folder_selected)
        self.folder_menu.set(NO_FOLDER_LABEL)
        self.folder_menu.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(footer, text="Tag (opsional, pisahkan dengan koma)").pack(anchor="w", padx=20)
        self.tags_entry = ctk.CTkEntry(footer, placeholder_text="contoh: promo, ramadhan, event")
        self.tags_entry.pack(fill="x", padx=20, pady=(2, 10))

        self.status_label = ctk.CTkLabel(footer, text="", text_color="gray", wraplength=420)
        self.status_label.pack()

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(pady=(6, 16))
        self.upload_btn = ctk.CTkButton(btn_row, text="Unggah", width=140, command=self._start_upload)
        self.upload_btn.grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btn_row, text="Batal", width=100, fg_color="transparent", border_width=1, command=self.destroy
        ).grid(row=0, column=1, padx=6)

        # ---------- Tengah: daftar file, MENGISI SISA RUANG ----------
        self.file_list_frame = ctk.CTkScrollableFrame(self, height=140)
        self.file_list_frame.pack(side="top", fill="both", expand=True, padx=20, pady=(6, 10))

        self.after(50, self._poll_ui_tasks)
        self._load_folders()

        # PENTING: grab_set() dipanggil PALING TERAKHIR (setelah semua widget
        # dibuat) dan didahului update_idletasks(). Kalau dipanggil terlalu
        # dini (window belum sempat "viewable" di layar), Tkinter melempar
        # TclError "grab failed: window not viewable" -- dan karena itu
        # terjadi di tengah __init__, SISA kode pembuatan widget di bawahnya
        # tidak pernah jalan, sehingga dialog tampil kosong tanpa isi.
        # try/except di sini murni jaring pengaman: kalaupun grab tetap
        # gagal di suatu kondisi, dialog tetap tampil & berfungsi penuh,
        # hanya saja tidak modal (interaksi ke jendela utama tidak terkunci).
        self.update_idletasks()
        try:
            self.grab_set()
        except Exception:
            pass

    def _poll_ui_tasks(self):
        self._ui_tasks.drain()
        if self.winfo_exists():
            self.after(50, self._poll_ui_tasks)

    # ---------- Folder ----------

    def _load_folders(self):
        threading.Thread(target=self._fetch_folders, daemon=True).start()

    def _fetch_folders(self):
        try:
            folders = self.master_app.api.list_folders()
            self._ui_tasks.push(lambda: self._set_folder_options(folders))
        except Exception:
            pass  # daftar folder gagal dimuat -> tetap bisa unggah tanpa folder

    def _set_folder_options(self, folders):
        if not self.winfo_exists():
            return
        self.folder_map = {f["name"]: f["id"] for f in folders}
        values = [NO_FOLDER_LABEL] + list(self.folder_map.keys()) + [CREATE_FOLDER_LABEL]
        current = self.folder_menu.get()
        self.folder_menu.configure(values=values)
        if current not in values:
            self.folder_menu.set(NO_FOLDER_LABEL)

    def _on_folder_selected(self, value):
        if value == CREATE_FOLDER_LABEL:
            self._create_new_folder()
        elif value == NO_FOLDER_LABEL:
            self.selected_folder_id = None
        else:
            self.selected_folder_id = self.folder_map.get(value)

    def _create_new_folder(self):
        dialog = ctk.CTkInputDialog(title="Folder Baru", text="Nama folder baru:")
        name = dialog.get_input()
        if not name or not name.strip():
            self.folder_menu.set(NO_FOLDER_LABEL)
            self.selected_folder_id = None
            return
        name = name.strip()
        self.folder_menu.configure(state="disabled")
        self.folder_menu.set("Membuat folder...")
        threading.Thread(target=self._do_create_folder, args=(name,), daemon=True).start()

    def _do_create_folder(self, name):
        try:
            folder = self.master_app.api.create_folder(name)
            self._ui_tasks.push(lambda: self._on_folder_created(folder))
        except ApiError as e:
            msg = e.message
            self._ui_tasks.push(lambda: self._on_folder_create_failed(msg))
        except Exception:
            self._ui_tasks.push(lambda: self._on_folder_create_failed("Tidak dapat terhubung ke server"))

    def _on_folder_created(self, folder):
        if not self.winfo_exists():
            return
        self.folder_menu.configure(state="normal")
        self.folder_map[folder["name"]] = folder["id"]
        values = [NO_FOLDER_LABEL] + list(self.folder_map.keys()) + [CREATE_FOLDER_LABEL]
        self.folder_menu.configure(values=values)
        self.folder_menu.set(folder["name"])
        self.selected_folder_id = folder["id"]

    def _on_folder_create_failed(self, message):
        if not self.winfo_exists():
            return
        self.folder_menu.configure(state="normal")
        self.folder_menu.set(NO_FOLDER_LABEL)
        self.selected_folder_id = None
        self.status_label.configure(text=f"Gagal membuat folder: {message}", text_color="#e74c3c")

    # ---------- Pilih file ----------

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

    # ---------- Upload ----------

    def _start_upload(self):
        if not self.files:
            self.status_label.configure(text="Pilih minimal satu file terlebih dahulu", text_color="#e74c3c")
            return
        self.upload_btn.configure(state="disabled", text="Mengunggah...")
        tags = self.tags_entry.get().strip()
        folder_id = self.selected_folder_id
        threading.Thread(target=self._do_upload, args=(list(self.files), tags, folder_id), daemon=True).start()

    def _do_upload(self, files, tags, folder_id):
        success, failed = 0, 0
        total = len(files)
        for path in files:
            try:
                self.master_app.api.upload_poster(path, tags, folder_id)
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
