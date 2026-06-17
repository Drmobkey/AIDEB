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
    Fungsi utilitas untuk menghapus file yang umurnya sudah lebih dari 7 hari di server.
    """
    now = time.time()
    cutoff = now - (max_age_days * 86400) # 86400 adalah jumlah detik dalam 1 hari
    
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            # Ambil waktu modifikasi terakhir file tersebut
            file_modified_time = os.path.getmtime(file_path)
            
            # Jika waktu modifikasi file lebih tua daripada batas cutoff, hapus!
            if file_modified_time < cutoff:
                try:
                    os.remove(file_path)
                    print(f"--- [AUTO CLEAN] Menghapus file usang: {filename} ---")
                except Exception as e:
                    print(f"Gagal menghapus file {filename}: {e}")

@predict_bp.route('/api/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "Permintaan tidak sah, tidak ada bagian file!"}), 400
    
    file = request.files['file']
    
    nama_pasien = request.form.get('nama_pasien', 'Anonim')
    no_rm = request.form.get('no_rm', '-')
    
    validation_result = process_upload_validation(file)
    if not validation_result["success"]:
        return jsonify ({"error": validation_result["message"]}),validation_result["status_code"]
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # PANGGIL AI UNTUK PREDIKSI NYATA
    ai_result = run_ai_prediction(filepath)
    
    if ai_result["success"]:
        return jsonify({
            "status": "success",
            "analysis_id": f"DETUJI-{uuid.uuid4().hex[:8].upper()}",
            "nama_pasien": nama_pasien,
            "no_rm": no_rm,
            "saved_filename": filename,
            "prediction": ai_result["prediction"],
            "confidence": min(round(ai_result["confidence"] * 100, 2), 99.99),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": ai_result.get("message", "File gambar CT Scan berhasil dianalisis"),
        }), 200
    else:
        error_response = {
            "status": "error",
            "message": ai_result.get("message", "Gagal memproses file gambar CT Scan"),
            "saved_filename": filename
        }
        if "confidence" in ai_result:
            error_response["confidence"] = min(round(ai_result["confidence"] * 100, 2), 99.99)
        return jsonify(error_response), 400