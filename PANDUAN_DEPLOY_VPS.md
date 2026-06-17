# Panduan Deployment Proyek DETUJI-CT ke VPS Berdampingan dengan Projek Lain

Dokumen ini menjelaskan langkah-langkah untuk mengunggah dan menjalankan proyek **DETUJI-CT** di VPS Anda menggunakan Docker, berdampingan dengan proyek existing yang sudah berjalan di port `5001` (backend) dan `3000` (frontend).

---

## ⚠️ Hal Penting Sebelum Memulai (PENTING!)

Karena frontend Next.js menggunakan *Client-side Fetching* (permintaan API dipicu langsung dari browser pengguna), pengaturan `NEXT_PUBLIC_API_URL` **tidak boleh** menggunakan `localhost` jika ingin diakses dari luar VPS. 
* Hubungkan frontend ke alamat IP Publik VPS Anda (contoh: `http://103.xxx.xx.xx:5002`).

---

## Metode 1: Menggunakan Git (Sangat Direkomendasikan)
Metode ini adalah cara paling bersih dan mudah untuk memperbarui kode di kemudian hari.

### Langkah 1: Push Proyek Lokal ke GitHub/GitLab
1. Buat repository baru di GitHub (disarankan bersifat **Private** karena ada model AI dan data sensitif).
2. Di komputer lokal Anda (menggunakan Git Bash/Terminal), jalankan:
   ```bash
   git init
   git add .
   git commit -m "feat: setup docker production ports 5002 and 3001"
   git branch -M main
   git remote add origin <URL_REPOSITORY_GITHUB_ANDA>
   git push -u origin main
   ```

### Langkah 2: Clone di VPS Anda
1. Masuk ke VPS Anda menggunakan SSH:
   ```bash
   ssh root@<IP_VPS_ANDA>
   ```
2. Arahkan ke folder tempat Anda menyimpan projek-projek (misalnya `/var/www/` atau `/home/`):
   ```bash
   cd /var/www
   ```
3. Clone repository dari GitHub:
   ```bash
   git clone <URL_REPOSITORY_GITHUB_ANDA> detuji-ct
   ```
4. Masuk ke direktori projek:
   ```bash
   cd detuji-ct
   ```

---

## Metode 2: Menggunakan File Transfer (ZIP & SFTP)
Jika Anda tidak ingin menggunakan Git, Anda bisa mengompres dan mengirim berkas secara langsung.

### Langkah 1: Kompres Proyek Lokal
Kompres seluruh isi folder `DETUJI-CT` menjadi file `.zip` atau `.tar.gz`.
> **PENTING:** Jangan ikut sertakan folder `node_modules` (di frontend) atau folder `.next` (jika ada) serta virtual environment `venv` karena ukuran file akan sangat besar dan tidak dibutuhkan (Docker akan menginstalnya kembali di dalam container).

### Langkah 2: Unggah ke VPS
Gunakan aplikasi SFTP seperti **FileZilla**, **MobaXterm**, atau **WinSCP**:
1. Hubungkan ke VPS Anda menggunakan IP, username (`root` atau lainnya), dan password / SSH Key.
2. Buat folder baru di VPS, misalnya `/var/www/detuji-ct`.
3. Unggah file zip yang sudah dibuat ke dalam folder tersebut.

### Langkah 3: Ekstrak di VPS
Di terminal VPS Anda, jalankan perintah untuk mengekstrak:
```bash
cd /var/www/detuji-ct
unzip nama_file_proyek.zip
```
*(Jika perintah `unzip` belum terinstall, install dengan `apt install unzip` pada Ubuntu/Debian).*

---

## Langkah 3: Menyiapkan File `.env` di VPS

Di dalam folder `/var/www/detuji-ct/backend`, buat file `.env` untuk konfigurasi admin backend:
```bash
nano backend/.env
```
Isi dengan kredensial admin Anda:
```env
PORT=5002
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password_aman_anda
```
*(Tekan `CTRL + O`, lalu `Enter` untuk menyimpan, dan `CTRL + X` untuk keluar dari editor nano).*

---

## Langkah 4: Membangun & Menjalankan Docker Container

### 1. Build & Run dengan IP VPS Publik
Untuk membangun container di VPS, Anda perlu meneruskan alamat IP VPS Anda ke argumen build frontend agar Next.js dapat menembak API backend dengan benar:

Jalankan perintah ini di direktori root `detuji-ct` (tempat file `docker-compose.yml` berada):
```bash
docker compose build --build-arg NEXT_PUBLIC_API_URL=http://<IP_VPS_ANDA>:5002
```
*Ganti `<IP_VPS_ANDA>` dengan alamat IP publik VPS Anda.*

### 2. Jalankan Container di Background
Setelah proses build selesai, jalankan container dengan perintah:
```bash
docker compose up -d
```

### 3. Memastikan Container Berjalan Berdampingan
Anda dapat melihat daftar container yang aktif dengan perintah:
```bash
docker ps
```
Anda akan melihat container dari kedua proyek berjalan bersamaan tanpa bentrok:
* **Proyek Lama (sides ct)**: berjalan di port host `5001` (backend) dan `3000` (frontend).
* **Proyek Baru (detuji ct)**: berjalan di port host `5002` (backend) dan `3001` (frontend).

---

## Panduan Troubleshooting & Perawatan

### Memeriksa Log Container jika Terjadi Error
Jika salah satu container tidak berjalan atau error, cek lognya:
```bash
# Log backend detuji
docker logs -f detuji-backend

# Log frontend detuji
docker logs -f detuji-frontend
```

### Cara Memperbarui Kode di VPS di Masa Mendatang
Jika Anda melakukan perubahan kode di komputer lokal Anda, lakukan langkah berikut:
1. **Lokal**: Push perubahan ke GitHub (`git push`).
2. **VPS**: Tarik kode terbaru dan build ulang:
   ```bash
   git pull
   docker compose down
   docker compose build --build-arg NEXT_PUBLIC_API_URL=http://<IP_VPS_ANDA>:5002
   docker compose up -d
   ```
