import os
import cv2
import numpy as np
import pydicom
from PIL import Image
from config import Config

# ============================================================
# AIDEB — AI-based Epilepsy Detection via Brain Imaging
# Model: YOLOv8n-cls (Ultralytics) | Classes: epilepsi / normal
# ============================================================

MODEL = None

def load_ai_model():
    """Memuat model YOLOv8n-cls dari file .pt ke memori."""
    global MODEL
    if MODEL is None:
        if os.path.exists(Config.MODEL_PATH):
            try:
                from ultralytics import YOLO
                MODEL = YOLO(Config.MODEL_PATH)
                print(f"--- [SUKSES] Model AIDEB (YOLOv8) Berhasil Dimuat dari {Config.MODEL_PATH} ---")
            except Exception as e:
                print(f"--- [ERROR] Gagal memuat model: {e} ---")
        else:
            print(f"--- [PERINGATAN] File model tidak ditemukan di {Config.MODEL_PATH} ---")
    return MODEL


def allowed_file(filename):
    """Cek apakah ekstensi file diizinkan."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def is_not_medical_image(file_stream, threshold=None):
    """
    Validasi terpadu apakah gambar terlihat seperti citra medis (MRI otak):
    1. Harus berupa gambar grayscale / near-grayscale (berdasarkan deviasi warna RGB).
    2. Harus memiliki struktur visual khas MRI otak (4 sudut hitam pekat & tengah memiliki objek terang).
    Mengembalikan True jika gambar TIDAK VALID sebagai citra MRI.
    """
    if threshold is None:
        threshold = getattr(Config, 'COLOR_THRESHOLD', 10.0)

    # 1. Skip validasi untuk DICOM — sudah pasti medis
    filename = getattr(file_stream, 'filename', '')
    if filename and filename.rsplit('.', 1)[-1].lower() == 'dcm':
        return False

    # 2. Baca gambar dari memory stream
    file_bytes = np.frombuffer(file_stream.read(), np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # 3. Reset pointer ke awal agar bisa dibaca ulang
    file_stream.seek(0)

    if img_bgr is None:
        return True

    # 4. Hitung rata-rata deviasi antar channel warna (R, G, B) untuk cek grayscale
    b, g, r = cv2.split(img_bgr)
    diff_rg = np.abs(r.astype(np.int16) - g.astype(np.int16))
    diff_rb = np.abs(r.astype(np.int16) - b.astype(np.int16))
    diff_gb = np.abs(g.astype(np.int16) - b.astype(np.int16))
    mean_diff = (np.mean(diff_rg) + np.mean(diff_rb) + np.mean(diff_gb)) / 3.0

    # Jika rata-rata selisih warna di atas threshold → terlalu berwarna → bukan medis
    if mean_diff > threshold:
        return True

    # 5. Validasi struktur khas MRI (sudut hitam pekat & bagian tengah ada objek terang)
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    corner_thresh = getattr(Config, 'MRI_CORNER_THRESHOLD', 50.0)
    center_thresh = getattr(Config, 'MRI_CENTER_THRESHOLD', 15.0)

    # Cek kecerahan di 4 sudut gambar (2% area sudut paling pojok)
    cw, ch = max(int(w * 0.02), 1), max(int(h * 0.02), 1)
    corners = [
        gray[0:ch, 0:cw],       # Kiri atas
        gray[0:ch, w-cw:w],     # Kanan atas
        gray[h-ch:h, 0:cw],     # Kiri bawah
        gray[h-ch:h, w-cw:w]    # Kanan bawah
    ]
    for corner in corners:
        if np.mean(corner) > corner_thresh:
            return True  # Sudut terlalu terang (bukan background hitam MRI)

    # Cek kecerahan di area tengah (40% area tengah)
    cx_start, cx_end = int(w * 0.3), int(w * 0.7)
    cy_start, cy_end = int(h * 0.3), int(h * 0.7)
    center_area = gray[cy_start:cy_end, cx_start:cx_end]
    if np.mean(center_area) < center_thresh:
        return True  # Bagian tengah terlalu gelap (bukan objek otak)

    return False


def process_upload_validation(file):
    """Validasi lengkap file upload sebelum diproses model."""
    if file.filename == '':
        return {
            "success": False,
            "message": "Nama file tidak boleh kosong!",
            "status_code": 400
        }

    if not allowed_file(file.filename):
        return {
            "success": False,
            "message": f"Format file tidak diizinkan! Hanya menerima: {', '.join(Config.ALLOWED_EXTENSIONS)}",
            "status_code": 400
        }

    # Cek ukuran file
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)

    if file_length > Config.MAX_CONTENT_LENGTH:
        max_mb = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
        return {
            "success": False,
            "message": f"Ukuran file terlalu besar! Maksimal {max_mb:.0f} MB.",
            "status_code": 413
        }

    # Validasi konten gambar (bukan foto biasa / terlalu berwarna)
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext != 'dcm':
        if is_not_medical_image(file):
            return {
                "success": False,
                "message": "File ditolak! Gambar tidak dikenali sebagai citra medis MRI/CT Scan yang valid.",
                "status_code": 400
            }

    return {"success": True, "status_code": 200}


def read_image_file(file_path):
    """
    Membaca file gambar (standar atau DICOM) dan mengembalikan array RGB.
    Digunakan untuk keperluan konversi DICOM di PDF, bukan untuk prediksi YOLO
    (YOLO menerima path file langsung).
    """
    ext = file_path.split('.')[-1].lower()

    if ext == 'dcm':
        ds = pydicom.dcmread(file_path)
        img_array = ds.pixel_array

        # Normalisasi ke uint8
        img_min, img_max = np.min(img_array), np.max(img_array)
        if img_max > img_min:
            img_array = ((img_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)
        else:
            img_array = np.zeros_like(img_array, dtype=np.uint8)

        # Konversi ke RGB 3-channel
        if len(img_array.shape) == 2:
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif len(img_array.shape) == 3:
            if img_array.shape[2] == 1:
                img_rgb = cv2.cvtColor(img_array[:, :, 0], cv2.COLOR_GRAY2RGB)
            elif img_array.shape[2] == 3:
                img_rgb = img_array
            elif img_array.shape[2] == 4:
                img_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            else:
                img_rgb = img_array
        else:
            img_rgb = img_array

        return img_rgb
    else:
        img_bgr = cv2.imread(file_path)
        if img_bgr is None:
            raise ValueError("Gagal membaca file gambar (file rusak atau format tidak didukung)")

        if len(img_bgr.shape) == 2:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_GRAY2RGB)
        elif len(img_bgr.shape) == 3:
            if img_bgr.shape[2] == 3:
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            elif img_bgr.shape[2] == 4:
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2RGB)
            else:
                img_rgb = img_bgr
        else:
            img_rgb = img_bgr

        return img_rgb


def _convert_dcm_to_png_temp(dcm_path):
    """
    Mengonversi file DICOM ke PNG sementara agar dapat dibaca oleh YOLO.
    Mengembalikan path file PNG sementara (wajib dihapus setelah selesai).
    """
    img_rgb = read_image_file(dcm_path)
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    temp_path = dcm_path + ".temp_yolo.png"
    cv2.imwrite(temp_path, img_bgr)
    return temp_path


def run_ai_prediction(file_path):
    """
    Menjalankan inferensi model YOLOv8n-cls AIDEB pada file gambar.
    
    Kelas output model:
        0 → epilepsi
        1 → normal

    Returns:
        dict dengan keys: success, prediction, confidence, is_doubtful, message
    """
    model = load_ai_model()
    if model is None:
        return {
            "success": False,
            "message": "Model AI AIDEB belum tersedia! Pastikan file yolotry.pt ada di model_storage/.",
            "status_code": 503
        }

    temp_path = None
    try:
        # 1. Tangani DICOM — konversi dulu ke PNG sementara
        predict_path = file_path
        if file_path.lower().endswith('.dcm'):
            temp_path = _convert_dcm_to_png_temp(file_path)
            predict_path = temp_path

        # 2. Jalankan prediksi YOLO
        #    imgsz=512 sesuai training, verbose=False untuk log bersih
        results = model.predict(
            source=predict_path,
            imgsz=512,
            verbose=False
        )

        result = results[0]

        # 3. Ambil probabilitas tiap kelas
        #    result.probs.data → tensor [prob_kelas_0, prob_kelas_1, ...]
        probs = result.probs.data.tolist()

        # Nama kelas dari model (sudah terurut sesuai index)
        # Model: {0: 'epilepsi', 1: 'normal'}
        class_names = result.names  # dict {0: 'epilepsi', 1: 'normal'}

        predicted_idx = int(result.probs.top1)
        confidence_score = float(probs[predicted_idx])

        # Label hasil prediksi (kapital untuk tampilan frontend)
        label_map = {
            'epilepsi': 'Epilepsi',
            'normal':   'Normal'
        }
        raw_label = class_names[predicted_idx].lower()
        hasil_diagnosis = label_map.get(raw_label, raw_label.title())

        # 4. Tentukan apakah hasil meragukan (confidence rendah)
        is_doubtful = confidence_score < 0.70

        return {
            "success": True,
            "prediction": hasil_diagnosis,
            "confidence": confidence_score,
            "is_doubtful": is_doubtful,
            "all_probs": {class_names[i]: round(probs[i], 4) for i in range(len(probs))},
            "message": (
                "Confidence rendah — Model AI ragu-ragu. Citra tidak dikenali dengan jelas sebagai MRI Epilepsi yang valid."
                if is_doubtful else
                "Citra berhasil dianalisis oleh model AIDEB."
            )
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Terjadi error saat analisis AI: {str(e)}"
        }
    finally:
        # Bersihkan file PNG sementara jika ada
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass