import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from config import Config
from services.pdf_service import generate_diagnosis_pdf

pdf_bp = Blueprint('pdf_bp', __name__)

@pdf_bp.route('/api/download-pdf', methods=['GET', 'POST'])
def download_pdf():
    # 1. Kumpulkan data dari JSON, Form, atau Query params (GET)
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
    else:
        data = request.args.to_dict()
        
    # 2. Validasi field yang diperlukan untuk laporan PDF
    required_fields = ['analysis_id', 'nama_pasien', 'no_rm', 'saved_filename', 'prediction', 'confidence', 'timestamp']
    for field in required_fields:
        val = data.get(field)
        if val is None or str(val).strip() == '':
            return jsonify({"error": f"Parameter '{field}' wajib diisi!"}), 400
            
    # 3. Cari gambar scan utama (representatif) di server
    image_filename = data['saved_filename']
    image_path = os.path.join(Config.UPLOAD_FOLDER, image_filename)
    if not os.path.exists(image_path):
        return jsonify({"error": "Berkas citra medis MRI tidak ditemukan di server!"}), 404

    # 4. Parse per_image_results jika ada (multifile)
    per_image_results = data.get('per_image_results', [])
    if isinstance(per_image_results, str):
        try:
            per_image_results = json.loads(per_image_results)
        except (json.JSONDecodeError, TypeError):
            per_image_results = []

    # Validasi bahwa file-file lampiran ada di server
    validated_per_image = []
    for item in per_image_results:
        item_path = os.path.join(Config.UPLOAD_FOLDER, item.get('filename', ''))
        if os.path.exists(item_path):
            validated_per_image.append(item)

    # 5. Buat nama berkas PDF yang aman diikuti no rekam medis dan nama pasien
    safe_name = "".join(c for c in str(data['nama_pasien']) if c.isalnum() or c in (' ', '_', '-')).strip()
    safe_rm = "".join(c for c in str(data['no_rm']) if c.isalnum() or c in (' ', '_', '-')).strip()
    
    # Ubah spasi menjadi underscore
    safe_name = safe_name.replace(' ', '_')
    safe_rm = safe_rm.replace(' ', '_')
    
    # Nama berkas PDF formal
    pdf_filename = f"Hasil_Analisis_{safe_rm}_{safe_name}.pdf"
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, pdf_filename)
    
    try:
        # Panggil service ReportLab untuk merakit PDF
        generate_diagnosis_pdf(data, image_path, pdf_path, per_image_results=validated_per_image)
        
        # Kirim file PDF sebagai attachment download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"error": f"Gagal membuat laporan PDF: {str(e)}"}), 500
