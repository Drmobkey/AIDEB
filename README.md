<div align="center">
  <img src="https://img.icons8.com/color/96/000000/brain.png" alt="AIDEB Logo" width="100"/>
  
  # 🧠 AIDEB - Artificial Intelligence untuk Deteksi Epilepsi
  
  <p align="center">
    <strong>Sistem Deteksi Dini Epilepsi Berbasis Citra MRI Otak menggunakan YOLOv8</strong>
  </p>
  
  <p align="center">
    <a href="#-fitur-utama">Fitur</a> • 
    <a href="#-tangkapan-layar">Tangkapan Layar</a> • 
    <a href="#-teknologi-yang-digunakan">Teknologi</a> • 
    <a href="#-struktur-repositori">Arsitektur</a> • 
    <a href="#-panduan-instalasi-development-lokal">Instalasi</a>
  </p>
</div>

---

## 🌟 Tentang Proyek

**AIDEB (Artificial Intelligence for Diagnosis of Epilepsy based on Brain MRI)** adalah platform aplikasi cerdas yang dapat mendeteksi kondisi epilepsi dari citra Magnetic Resonance Imaging (MRI) otak. Aplikasi ini dikembangkan untuk membantu tenaga medis maupun radiolog dalam mengidentifikasi secara cepat dan akurat apakah pasien memiliki kondisi otak normal atau mengindikasikan adanya kelainan neurologis terkait epilepsi.

Dibekali dengan model _Deep Learning_ **YOLOv8**, AIDEB mampu menganalisa citra medis (PNG, JPG, JPEG, hingga DICOM) dalam hitungan detik dan secara otomatis menghasilkan **Laporan Radiologi berformat PDF** yang siap diunduh.

---

## ✨ Fitur Utama

- 🔐 **Autentikasi Aman**: Sistem login yang simpel dan efisien dengan token proteksi untuk keamanan data pasien.
- 🖼️ **Dukungan Berbagai Format Citra**: Mampu memproses citra standar (JPG/PNG) maupun citra medis standar industri (DICOM).
- 🚀 **Analisis AI Cepat & Akurat**: Prediksi kondisi Normal/Epilepsi beserta metrik _Confidence Score_ secara _realtime_ menggunakan PyTorch dan YOLOv8.
- 📄 **Cetak Laporan Otomatis**: Generator PDF laporan hasil analisis (Radiology Report) yang rapi, lengkap dengan nama pasien dan anjuran medis.
- 🎨 **Antarmuka Modern & Responsif**: UI/UX medis premium dengan warna gradasi `Teal (#0A7C6E)` yang memukau, modern, dan ramah pengguna.
- 🐳 **Optimal untuk VPS**: Disusun di atas _container_ Docker yang dirancang hemat _resource_ memori dan prosesor (ideal untuk server VPS RAM 4GB).

---

## 📸 Tangkapan Layar

<div align="center">

### 1. Halaman Autentikasi (Login)
<img src="./frontend/screenshoot/login.png" alt="AIDEB Login" width="800" style="border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1);"/>
<br/><br/>

### 2. Dashboard Utama & Area Unggah
<img src="./frontend/screenshoot/dashboard.png" alt="AIDEB Dashboard" width="800" style="border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1);"/>
<br/><br/>

### 3. Hasil Analisis AI
<img src="./frontend/screenshoot/result.png" alt="AIDEB Result" width="800" style="border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1);"/>
<br/><br/>

### 4. Laporan PDF Cetak (Radiologi)
<img src="./frontend/screenshoot/pdf_result.png" alt="AIDEB PDF Report" width="800" style="border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1);"/>

</div>

---

## 🛠️ Teknologi yang Digunakan

AIDEB memisahkan arsitektur *Frontend* dan *Backend* untuk skalabilitas, performa, dan pemeliharaan yang lebih mudah.

### 🎨 Frontend (Client)
- **Framework:** [Next.js](https://nextjs.org/) (React)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/) dengan palet warna medis Teal (`#0A7C6E`) dan antarmuka *Glassmorphism*.
- **Icons:** [Lucide React](https://lucide.dev/)
- **Deployment:** Docker / Node.js
- **Fitur Utama:** Client-side routing, proteksi *State/Token*, komponen reaktif.

### ⚙️ Backend (Server / AI)
- **Framework:** [Flask](https://flask.palletsprojects.com/) (Python)
- **AI / Deep Learning:** [PyTorch](https://pytorch.org/) (CPU-only untuk optimasi server ringan) & [Ultralytics YOLOv8](https://docs.ultralytics.com/) (`yolov8n-cls`)
- **Medical Imaging:** `pydicom` untuk ekstraksi visual dari berkas MRI format standar rumah sakit (.dcm).
- **PDF Generation:** `FPDF2`
- **Deployment:** Docker / Gunicorn / Waitress
- **Fitur Utama:** API berbasis REST, pengelolaan arsip temporer (*temp file handling*), manajemen *Cross-Origin Resource Sharing* (CORS).

---

## 📁 Struktur Repositori

```text
AIDEB/
├── backend/                  # REST API Server & AI Model
│   ├── app.py                # Entry point aplikasi Flask
│   ├── config.py             # Konfigurasi _path_ dan setelan variabel
│   ├── model_storage/        # Penyimpanan model YOLOv8 (yolotry.pt)
│   ├── routes/               # Rute dan titik akhir (endpoint) komunikasi API
│   ├── services/             # Logika bisnis inti (AI Service, PDF Service)
│   ├── Dockerfile            # Blueprint pembangunan citra Docker Backend
│   └── requirement.txt       # Daftar dependensi modul Python
├── frontend/                 # Aplikasi Antarmuka Pengguna
│   ├── src/app/              # Next.js App Router (Halaman Utama, Login, CSS, dll)
│   ├── src/components/       # Komponen UI mandiri
│   ├── src/config.js         # Konfigurasi komunikasi ke server Backend
│   ├── screenshoot/          # Kumpulan tangkapan layar antarmuka
│   ├── Dockerfile            # Blueprint pembangunan citra Docker Frontend
│   └── package.json          # Daftar paket NPM Next.js
├── docker-compose.yml        # Berkas orkestrasi integrasi sistem via Docker
└── PANDUAN_DEPLOY_VPS.md     # Arahan terperinci mengenai tahapan _deploy_ di Server VPS
```

---

## 🚀 Panduan Instalasi (Development Lokal)

### 1. Kloning Repositori
```bash
git clone https://github.com/username/aideb.git
cd aideb
```

### 2. Menjalankan Server Backend (API)
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirement.txt
python app.py
```
> *Server API akan berjalan pada `http://localhost:5003`*

### 3. Menjalankan Aplikasi Frontend
Buka terminal interaktif yang baru:
```bash
cd frontend
npm install
npm run dev
```
> *Aplikasi klien akan di-host pada `http://localhost:3000`*

---

## 🐳 Deployment (VPS / Production)

Aplikasi ini telah dirancang kompatibel untuk diunggah pada perangkat peladen (VPS) dengan arsitektur _Container_ menggunakan **Docker Compose**. Kapasitas maksimum memori juga telah dimutakhirkan secara dinamis (Backend <1.5GB, Frontend <500MB).

```bash
# Menjalankan seluruh sistem di latar belakang
docker compose up -d

# Melakukan pengecekan status container aplikasi
docker compose ps

# Membaca log eksekusi secara real-time
docker compose logs -f aideb-backend
```

*Untuk panduan menyeluruh seputar konfigurasi domain SSL, perutean Proxy Nginx, dan pengelolaan memori _Swap_, silakan merujuk kepada berkas pendamping: **`PANDUAN_DEPLOY_VPS.md`**.*

---

<div align="center">
  <br/>
  <p>Dibuat dengan ❤️ untuk Masa Depan Inovasi Kesehatan Indonesia</p>
  <p><b>AIDEB Team © 2026</b></p>
</div>
