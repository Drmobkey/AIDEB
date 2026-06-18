import os
import uuid
import time
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from config import Config
from services.ai_service import process_upload_validation, run_ai_prediction

predict_bp = Blueprint('predict_bp', __name__)


def auto_clean_old_files(folder_path, max_age_days=7):
    """
    Menghapus file di folder uploads yang umurnya sudah melebihi max_age_days hari.
    """
    now = time.time()
    cutoff = now - (max_age_days * 86400)  # 86400 detik = 1 hari

    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_modified_time = os.path.getmtime(file_path)
                if file_modified_time < cutoff:
                    try:
                        os.remove(file_path)
                        print(f"--- [AUTO CLEAN] Menghapus file usang: {filename} ---")
                    except Exception as e:
                        print(f"Gagal menghapus file {filename}: {e}")


@predict_bp.route('/api/predict', methods=['POST'])
def predict():
    """
    Endpoint utama untuk analisis citra MRI menggunakan model AIDEB (YOLOv8n-cls).
    Menerima file gambar (PNG/JPG/DICOM) dan mengembalikan hasil klasifikasi epilepsi/normal.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Permintaan tidak sah, tidak ada bagian file!"}), 400

    file = request.files['file']

    # Ambil data pasien dari form (opsional)
    nama_pasien = request.form.get('nama_pasien', 'Anonim')
    no_rm = request.form.get('no_rm', '-')

    # 1. Validasi file (ekstensi, ukuran, konten medis)
    validation_result = process_upload_validation(file)
    if not validation_result["success"]:
        return jsonify({"error": validation_result["message"]}), validation_result["status_code"]

    # 2. Simpan file ke folder uploads
    filename = secure_filename(file.filename)
    # Tambahkan UUID agar tidak ada konflik nama file
    unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    file.save(filepath)

    # 3. Bersihkan file lama secara otomatis (background housekeeping)
    auto_clean_old_files(Config.UPLOAD_FOLDER)

    # 4. Jalankan model AIDEB untuk prediksi
    ai_result = run_ai_prediction(filepath)

    if ai_result["success"]:
        response = {
            "status":         "success",
            "analysis_id":    f"AIDEB-{uuid.uuid4().hex[:8].upper()}",
            "nama_pasien":    nama_pasien,
            "no_rm":          no_rm,
            "saved_filename": unique_filename,
            "prediction":     ai_result["prediction"],
            "confidence":     min(round(ai_result["confidence"] * 100, 2), 99.99),
            "is_doubtful":    ai_result.get("is_doubtful", False),
            "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message":        ai_result.get("message", "Citra berhasil dianalisis oleh model AIDEB."),
        }
        # Sertakan distribusi probabilitas semua kelas (opsional, untuk debugging/info)
        if "all_probs" in ai_result:
            response["all_probs"] = ai_result["all_probs"]

        return jsonify(response), 200

    else:
        error_response = {
            "status":         "error",
            "message":        ai_result.get("message", "Gagal memproses citra MRI."),
            "saved_filename": unique_filename
        }
        if "confidence" in ai_result:
            error_response["confidence"] = min(round(ai_result["confidence"] * 100, 2), 99.99)
        return jsonify(error_response), 400