"""
Utilitas kecil untuk komunikasi aman antara background thread dan thread utama
Tkinter/CustomTkinter.

CATATAN PENTING (pelajaran dari versi sebelumnya): memanggil widget.after()
LANGSUNG dari background thread bisa memicu
'RuntimeError: main thread is not in main loop' karena Tcl tidak selalu
thread-safe di semua kondisi. Pola yang benar-benar aman: background thread
hanya menaruh tugas ke queue.Queue (aman dipanggil dari thread mana pun),
lalu thread utama yang menjadwalkan after() untuk mengosongkan queue
tersebut secara berkala.
"""
import queue


class UiTaskQueue:
    def __init__(self):
        self._q = queue.Queue()

    def push(self, callback) -> None:
        """Dipanggil dari background thread untuk menjadwalkan `callback`
        agar dijalankan nanti di thread utama."""
        self._q.put(callback)

    def drain(self) -> None:
        """Dipanggil dari thread utama (lewat widget.after) untuk menjalankan
        semua callback yang tertunda."""
        while True:
            try:
                callback = self._q.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except Exception:
                pass
