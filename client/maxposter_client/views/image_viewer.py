import io
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from ..api_client import ApiError
from ..thread_utils import UiTaskQueue

MAX_VIEW_SIZE = (900, 700)


class ImageViewer(ctk.CTkToplevel):
    def __init__(self, master_app, poster, on_deleted):
        super().__init__(master_app)
        self.master_app = master_app
        self.poster = poster
        self.on_deleted = on_deleted
        self._full_bytes = None  # disimpan setelah dimuat, dipakai ulang saat unduh
        self._ui_tasks = UiTaskQueue()

        self.title(poster["original_filename"])
        self.geometry("700x620")
        self.transient(master_app)
        self.grab_set()

        is_landscape = poster["category"] == "landscape"
        info = (
            f'{poster["width"]} x {poster["height"]} px  •  '
            f'{self._format_size(poster["filesize"])}  •  '
            f'{"Landscape" if is_landscape else "Potrait"}'
        )
        ctk.CTkLabel(self, text=poster["original_filename"], font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(16, 2)
        )
        ctk.CTkLabel(self, text=info, text_color="gray").pack(pady=(0, 10))

        self.image_label = ctk.CTkLabel(self, text="Memuat gambar...")
        self.image_label.pack(fill="both", expand=True, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack()

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(6, 16))
        self.download_btn = ctk.CTkButton(btn_row, text="Unduh ke Komputer", command=self._download)
        self.download_btn.grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btn_row, text="Hapus Poster", fg_color="#e74c3c", hover_color="#c0392b", command=self._confirm_delete
        ).grid(row=0, column=1, padx=6)
        ctk.CTkButton(
            btn_row, text="Tutup", fg_color="transparent", border_width=1, command=self.destroy
        ).grid(row=0, column=2, padx=6)

        self.after(50, self._poll_ui_tasks)
        threading.Thread(target=self._load_full_image, daemon=True).start()

    def _poll_ui_tasks(self):
        self._ui_tasks.drain()
        if self.winfo_exists():
            self.after(50, self._poll_ui_tasks)

    @staticmethod
    def _format_size(num_bytes):
        size = float(num_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _load_full_image(self):
        try:
            raw = self.master_app.api.get_file_bytes(self.poster["id"])
            img = Image.open(io.BytesIO(raw))
            img.load()
            preview = img.copy()
            preview.thumbnail(MAX_VIEW_SIZE)
            # PENTING: isi light_image DAN dark_image agar gambar tidak hilang saat
            # Windows dalam mode gelap (ini pernah jadi bug di versi sebelumnya).
            ctk_img = ctk.CTkImage(light_image=preview, dark_image=preview, size=preview.size)
            self._full_bytes = raw
            self._ui_tasks.push(lambda: self._set_image(ctk_img))
        except Exception:
            self._ui_tasks.push(self._set_load_error)

    def _set_image(self, ctk_img):
        if self.winfo_exists():
            self.image_label.configure(image=ctk_img, text="")
            self.image_label.image = ctk_img

    def _set_load_error(self):
        if self.winfo_exists():
            self.image_label.configure(text="Gagal memuat gambar", image=None)

    def _download(self):
        if self._full_bytes is None:
            messagebox.showinfo("Mohon tunggu", "Gambar masih dimuat, coba lagi sebentar.")
            return

        default_name = self.poster["original_filename"]
        ext = "." + default_name.rsplit(".", 1)[-1] if "." in default_name else ".jpg"
        save_path = filedialog.asksaveasfilename(
            title="Simpan poster",
            initialfile=default_name,
            defaultextension=ext,
            filetypes=[("Gambar", f"*{ext}"), ("Semua file", "*.*")],
        )
        if not save_path:
            return

        try:
            with open(save_path, "wb") as f:
                f.write(self._full_bytes)
            self.status_label.configure(text=f"Tersimpan di: {save_path}", text_color="#22c55e")
        except OSError as e:
            messagebox.showerror("Gagal menyimpan", f"Tidak dapat menyimpan file:\n{e}")

    def _confirm_delete(self):
        if messagebox.askyesno("Hapus Poster", f'Yakin ingin menghapus "{self.poster["original_filename"]}"?'):
            threading.Thread(target=self._do_delete, daemon=True).start()

    def _do_delete(self):
        try:
            self.master_app.api.delete_poster(self.poster["id"])
            self._ui_tasks.push(self._on_delete_success)
        except ApiError as e:
            msg = e.message
            self._ui_tasks.push(lambda: messagebox.showerror("Gagal", msg))
        except Exception:
            self._ui_tasks.push(lambda: messagebox.showerror("Gagal", "Tidak dapat menghapus poster."))

    def _on_delete_success(self):
        self.master_app.cache.invalidate(self.poster["id"])
        self.on_deleted()
        if self.winfo_exists():
            self.destroy()
