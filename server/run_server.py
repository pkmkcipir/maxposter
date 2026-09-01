"""
Entry point Maxposter Server.
Jalankan dengan: python run_server.py
Atau, setelah dibuild, cukup jalankan MaxposterServer.exe
"""
import socket


def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def main():
    import uvicorn
    from app.config import PORT
    from app.main import app

    lan_ip = get_lan_ip()

    print("=" * 56)
    print("   MAXPOSTER SERVER")
    print("=" * 56)
    print("  Server ini menyimpan semua data poster & akun.")
    print("  Biarkan jendela ini tetap terbuka selama dipakai.")
    print()
    print("  Alamat untuk PC LAIN di jaringan yang sama:")
    print(f"      http://{lan_ip}:{PORT}")
    print()
    print("  Alamat untuk komputer ini sendiri:")
    print(f"      http://127.0.0.1:{PORT}")
    print()
    print("  Masukkan salah satu alamat di atas ke aplikasi Maxposter")
    print("  (client) pada kolom 'Alamat server', ATAU buka langsung di")
    print("  browser (Chrome/Edge/Firefox) -- tidak perlu instal apa pun.")
    print("=" * 56)

    # Objek app dikirim langsung (bukan string "app.main:app") supaya tetap
    # berjalan benar ketika sudah dibundel sebagai .exe oleh PyInstaller.
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    main()
