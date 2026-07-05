import os
import uuid
import time
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from config import Config
from services.ai_service import process_upload_validation, run_ai_prediction

predict_bp = Blueprint('predict_bp', __name__)

MAX_FILES = 10  # Batas maksimal file yang boleh diunggah sekaligus


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


def _compute_dominant_prediction(per_image_results):
    """
    Hitung hasil dominan dari daftar per-image results menggunakan majority voting.
    Jika seri, pilih label dengan rata-rata confidence tertinggi.

    Returns:
        (dominant_label, dominant_avg_confidence, prediction_summary)
    """
    from collections import Counter

    labels = [r["prediction"] for r in per_image_results]
    counter = Counter(labels)

    # Cari label dengan jumlah terbanyak; jika seri, pilih confidence rata-rata tertinggi
    max_count = max(counter.values())
    candidates = [label for label, count in counter.items() if count == max_count]

    best_label = None
    best_avg_conf = -1.0

    for label in candidates:
        confs = [r["confidence"] for r in per_image_results if r["prediction"] == label]
        avg_conf = sum(confs) / len(confs)
        if avg_conf > best_avg_conf:
            best_avg_conf = avg_conf
            best_label = label

    prediction_summary = dict(counter)
    return best_label, round(best_avg_conf, 2), prediction_summary


@predict_bp.route('/api/predict', methods=['POST'])
def predict():
    """
    Endpoint utama untuk analisis citra MRI menggunakan model AIDEB (YOLOv8n-cls).
    Menerima satu atau banyak file gambar (PNG/JPG/DICOM) dan mengembalikan hasil klasifikasi.
    
    - Single file: field 'file' (backward-compatible)
    - Multiple files: field 'files' (array)
    
    Response selalu berformat multifile (per_image_results + dominant_prediction).
    """
    # 1. Kumpulkan file dari request (backward-compatible single + multifile)
    files = request.files.getlist('files')
    if not files or len(files) == 0:
        # Fallback: cek field 'file' tunggal (backward-compatible)
        single_file = request.files.get('file')
        if single_file:
            files = [single_file]
        else:
            return jsonify({"error": "Permintaan tidak sah, tidak ada bagian file!"}), 400

    if len(files) > MAX_FILES:
        return jsonify({
            "error": f"Maksimal {MAX_FILES} file yang boleh diunggah sekaligus! Anda mengunggah {len(files)} file."
        }), 400

    # Ambil data pasien dari form (opsional)
    nama_pasien = request.form.get('nama_pasien', 'Anonim')
    no_rm = request.form.get('no_rm', '-')

    # 2. Validasi, simpan, dan prediksi setiap file
    per_image_results = []
    saved_filenames = []
    validation_errors = []

    for idx, file in enumerate(files):
        # Validasi file
        validation_result = process_upload_validation(file)
        if not validation_result["success"]:
            validation_errors.append({
                "file_index": idx,
                "filename": file.filename,
                "error": validation_result["message"]
            })
            continue

        # Simpan file ke folder uploads
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        saved_filenames.append(unique_filename)

        # Jalankan prediksi YOLO
        ai_result = run_ai_prediction(filepath)

        if ai_result["success"]:
            per_image_results.append({
                "filename": unique_filename,
                "prediction": ai_result["prediction"],
                "confidence": min(round(ai_result["confidence"] * 100, 2), 99.99),
                "is_doubtful": ai_result.get("is_doubtful", False),
                "message": ai_result.get("message", "")
            })
        else:
            per_image_results.append({
                "filename": unique_filename,
                "prediction": "Error",
                "confidence": 0.0,
                "is_doubtful": True,
                "message": ai_result.get("message", "Gagal memproses citra.")
            })

    # 3. Bersihkan file lama secara otomatis (background housekeeping)
    auto_clean_old_files(Config.UPLOAD_FOLDER)

    # 4. Jika tidak ada file yang berhasil diproses sama sekali
    successful_results = [r for r in per_image_results if r["prediction"] not in ("Error",)]
    if len(successful_results) == 0:
        error_msg = "Tidak ada file yang berhasil diproses."
        if validation_errors:
            error_msg += f" {len(validation_errors)} file gagal validasi."
        return jsonify({
            "status": "error",
            "message": error_msg,
            "validation_errors": validation_errors
        }), 400

    # 5. Hitung hasil dominan
    dominant_label, dominant_confidence, prediction_summary = _compute_dominant_prediction(successful_results)

    # 6. Tentukan gambar representatif (gambar pertama yang sesuai hasil dominan)
    representative_filename = saved_filenames[0] if saved_filenames else ""
    for r in per_image_results:
        if r["prediction"] == dominant_label:
            representative_filename = r["filename"]
            break

    # 7. Cek apakah confidence dominan rendah
    is_doubtful = dominant_confidence < 70

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    analysis_id = f"AIDEB-{uuid.uuid4().hex[:8].upper()}"

    response = {
        "status":               "success",
        "analysis_id":          analysis_id,
        "nama_pasien":          nama_pasien,
        "no_rm":                no_rm,
        "saved_filename":       representative_filename,
        "prediction":           dominant_label,
        "confidence":           dominant_confidence,
        "is_doubtful":          is_doubtful,
        "total_files":          len(per_image_results),
        "prediction_summary":   prediction_summary,
        "per_image_results":    per_image_results,
        "timestamp":            timestamp,
        "message":              (
            "Confidence rendah — Model AI ragu-ragu. Citra tidak dikenali dengan jelas sebagai MRI Epilepsi yang valid."
            if is_doubtful else
            f"Berhasil menganalisis {len(per_image_results)} citra MRI."
        ),
    }

    if validation_errors:
        response["validation_errors"] = validation_errors

    return jsonify(response), 200