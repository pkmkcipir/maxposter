# Maxposter

Aplikasi Windows untuk menyimpan dan mengelola poster (landscape &
potrait) secara **online**, bisa diakses dari beberapa PC sekaligus dengan
login akun — lewat aplikasi desktop maupun langsung dari **browser**.
Dibangun dengan **Python + CustomTkinter** (client desktop) dan **FastAPI**
(server, sekaligus menyajikan antarmuka web), siap di-build otomatis
menjadi `.exe` lewat GitHub Actions.

## Fitur

- Login & registrasi akun dengan **persetujuan admin** — pendaftar baru berstatus menunggu sampai admin menyetujui langsung dari aplikasi (opsional juga dikunci dengan kode registrasi khusus admin)
- Banyak PC bisa konek ke satu server yang sama secara bersamaan (LAN/online)
- **Bisa diakses langsung dari browser** (Chrome/Edge/Firefox) dengan memasukkan alamat IP server — tidak perlu instal aplikasi apa pun, cukup buka di PC, HP, atau tablet mana saja yang satu jaringan
- Upload poster format **JPG, JPEG, PNG**
- **Deteksi otomatis landscape/potrait** berdasarkan ukuran gambar saat upload, langsung tersimpan ke folder masing-masing
- **Folder kustom**: buat folder sendiri (mis. "Promo Ramadhan", "Event Konser") langsung dari layar unggah untuk mengelompokkan poster sesuai kebutuhan, lalu filter galeri berdasarkan folder tersebut
- Pencarian cepat (nama file & tag) memakai SQLite full-text search
- Filter kategori (Semua / Landscape / Potrait) dan filter folder, bisa dikombinasikan
- Paginasi dengan pilihan **20 / 50 / 100** poster per halaman + tombol Sebelumnya/Berikutnya
- Cache thumbnail 2 lapis (disk + memori) supaya halaman galeri tetap ringan walau poster banyak
- Lihat poster ukuran penuh, unduh ke komputer, dan hapus
- Build otomatis ke `.exe` + installer Windows lewat GitHub Actions

## Arsitektur

Maxposter terdiri dari **server** dan **dua cara mengaksesnya**:

| Bagian | Fungsi | Dijalankan oleh |
|---|---|---|
| `MaxposterServer.exe` (server) | Menyimpan database akun & file poster, melayani semua client yang terhubung — sekaligus menyajikan antarmuka browser | Satu PC saja (jadi "pusat") |
| `Maxposter.exe` (client desktop) | Aplikasi desktop untuk login, upload, cari, lihat poster | PC yang sudah instal aplikasinya |
| Browser (Chrome/Edge/Firefox) | Antarmuka yang sama persis fungsinya, tanpa instalasi | PC/HP/tablet mana pun yang satu jaringan |

Semua cara akses (client desktop maupun browser) cukup diarahkan ke alamat
IP PC yang menjalankan `MaxposterServer.exe` — ini yang membuat aplikasinya
"online" dan poster yang diunggah dari satu tempat langsung terlihat di
tempat lain. Server bisa dijalankan di PC kantor biasa (LAN) atau di
VPS/cloud kalau mau diakses dari luar kantor.


## Struktur folder

```
maxposter/
├── server/                  # Backend (FastAPI) — jalankan di 1 PC sebagai pusat data
│   ├── app/                 # Kode API: auth, poster, folder, database, pencarian
│   ├── web/                 # Antarmuka browser (HTML/CSS/JS satu file, disajikan server)
│   ├── run_server.py        # Entry point (juga target build .exe)
│   ├── requirements.txt
│   └── maxposter_server.spec
├── client/                  # Aplikasi desktop (CustomTkinter) — diinstal ke semua PC
│   ├── maxposter_client/    # Kode aplikasi: login, galeri, upload, viewer
│   ├── main.py               # Entry point (juga target build .exe)
│   ├── requirements.txt
│   └── maxposter.spec
├── installer/
│   └── maxposter_setup.iss  # Skrip Inno Setup -> MaxposterSetup.exe
├── .github/workflows/
│   └── build.yml            # Build otomatis ke .exe setiap push ke GitHub
└── README.md
```

## Cara build otomatis jadi `.exe` lewat GitHub

1. Buat repository baru di GitHub, lalu push seluruh folder ini:
   ```
   git init
   git add .
   git commit -m "Maxposter awal"
   git branch -M main
   git remote add origin https://github.com/USERNAME/maxposter.git
   git push -u origin main
   ```
2. Buka tab **Actions** di repository GitHub Anda — workflow **"Build
   Maxposter Windows Executables"** akan otomatis berjalan.
3. Setelah selesai (±5-10 menit), buka hasil run tersebut lalu unduh di
   bagian **Artifacts**:
   - `Maxposter-Client-Portable` — folder aplikasi client siap pakai (tanpa instalasi)
   - `Maxposter-Setup-Installer` — **`MaxposterSetup.exe`**, installer client untuk didistribusikan ke staf
   - `Maxposter-Server-Portable` — folder `MaxposterServer.exe` untuk PC pusat data
4. Untuk membuat **GitHub Release** otomatis (lebih rapi untuk dibagikan),
   buat tag versi lalu push:
   ```
   git tag v1.0.0
   git push origin v1.0.0
   ```
   Release akan otomatis dibuat berisi ketiga file di atas siap diunduh.

Build juga bisa dipicu manual lewat tab Actions → pilih workflow → **Run
workflow**, tanpa perlu push kode baru.

## Cara pakai (setelah build selesai)

**Di PC yang jadi server (pusat data, cukup 1 PC):**
1. Salin folder `MaxposterServer` (hasil download Artifacts) ke lokasi permanen, misal `D:\MaxposterServer\`.
2. Jalankan `MaxposterServer.exe`. Jendela hitam (konsol) akan menampilkan alamat IP untuk PC lain, contoh:
   ```
   Alamat untuk PC LAIN di jaringan yang sama:
       http://192.168.1.10:8000
   ```
3. Biarkan jendela ini tetap terbuka selama aplikasi dipakai. Windows mungkin menampilkan konfirmasi **Windows Defender Firewall** saat pertama kali dijalankan — pilih **Allow access** (izinkan), khususnya untuk jaringan Private, supaya PC lain bisa terhubung.
4. Database (`maxposter.db`) dan folder `storage/` (isi poster) akan otomatis dibuat di folder yang sama dengan `MaxposterServer.exe` — cadangkan folder ini secara berkala.

**Di setiap PC staf (client desktop):**
1. Install `MaxposterSetup.exe`, lalu buka aplikasi **Maxposter**.
2. Pada layar login, isi **Alamat server** dengan alamat dari langkah server di atas (mis. `http://192.168.1.10:8000`).
3. Klik **"Belum punya akun? Daftar"** untuk membuat akun.

**Atau, tanpa instalasi apa pun — langsung dari browser:**
1. Di PC, HP, atau tablet yang satu jaringan dengan server, buka Chrome/Edge/Firefox.
2. Ketik alamat server di atas ke address bar (mis. `http://192.168.1.10:8000`) lalu Enter.
3. Halaman login Maxposter langsung tampil — daftar atau masuk seperti biasa. Semua fitur (unggah, cari, folder, kelola pengguna untuk admin) tersedia sama persis seperti aplikasi desktop.

## Persetujuan akun (admin)

- **Akun pertama yang mendaftar di sebuah server otomatis menjadi admin** dan langsung bisa dipakai — biasanya inilah akun yang Anda buat sendiri saat pertama kali menyiapkan server.
- **Setiap akun berikutnya** yang mendaftar berstatus **menunggu persetujuan** dan belum bisa login sampai admin menyetujuinya.
- Sebagai admin, buka tombol **"Kelola Pengguna"** di pojok kanan atas galeri (desktop maupun browser) untuk melihat daftar pendaftar yang menunggu, lalu klik **Setujui** atau **Tolak** untuk masing-masing.
- Kalau Anda sudah punya server yang berjalan sebelum fitur ini ada, saat di-update seluruh akun yang sudah ada otomatis tetap bisa login seperti biasa (tidak perlu disetujui ulang), dan akun yang paling pertama terdaftar otomatis dijadikan admin.

## Konfigurasi server (opsional)

Atur lewat environment variable sebelum menjalankan `MaxposterServer.exe`
(lewat System Properties → Environment Variables di Windows), atau saat
menjalankan dari source dengan `set NAMA=nilai` sebelum perintah run:

| Variable | Default | Keterangan |
|---|---|---|
| `MAXPOSTER_PORT` | `8000` | Port server |
| `MAXPOSTER_SECRET_KEY` | (nilai contoh bawaan) | **Wajib diganti** untuk produksi — dipakai menandatangani token login |
| `MAXPOSTER_REGISTER_CODE` | kosong (bebas daftar) | Jika diisi, pendaftaran akun baru wajib menyertakan kode ini — bagikan hanya ke staf yang berhak |
| `MAXPOSTER_STORAGE_DIR` | `storage/` di folder exe | Lokasi penyimpanan file poster |
| `MAXPOSTER_DB_PATH` | `maxposter.db` di folder exe | Lokasi file database |

## Menjalankan dari source code (untuk pengembangan)

Server:
```
cd server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_server.py
```

Client (di terminal terpisah):
```
cd client
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Build manual ke `.exe` tanpa GitHub Actions (harus dijalankan di Windows):
```
pip install pyinstaller
cd client && pyinstaller maxposter.spec --noconfirm
cd ../server && pyinstaller maxposter_server.spec --noconfirm
```

## Troubleshooting

- **PC lain tidak bisa konek ke server** — pastikan `MaxposterServer.exe`
  diizinkan lewat Windows Firewall, dan kedua PC berada di jaringan
  (WiFi/LAN) yang sama. Coba `ping <alamat-ip-server>` dari PC client untuk
  memastikan jaringan terhubung.
- **Lupa alamat IP server** — lihat kembali jendela konsol
  `MaxposterServer.exe` yang menampilkannya saat start, atau jalankan
  `ipconfig` di PC server dan cari "IPv4 Address".
- **Aplikasi client gagal login "Tidak dapat terhubung ke server"** — cek
  kembali alamat server (harus diawali `http://` dan menyertakan port,
  contoh `http://192.168.1.10:8000`) serta pastikan `MaxposterServer.exe`
  masih berjalan.
- **Build gagal di GitHub Actions** — buka log run yang gagal di tab
  Actions untuk detail errornya; penyebab paling umum adalah versi paket
  yang perlu disesuaikan di `requirements.txt`.

## Keamanan

- Password disimpan ter-enkripsi (hash bcrypt), bukan teks biasa.
- Sesi login pakai token JWT yang kedaluwarsa otomatis setelah 14 hari.
- Untuk pemakaian di luar jaringan lokal/kantor (lewat internet), sangat
  disarankan menambahkan HTTPS (mis. lewat reverse proxy seperti Caddy/Nginx)
  dan mengganti `MAXPOSTER_SECRET_KEY` dari nilai bawaan.
