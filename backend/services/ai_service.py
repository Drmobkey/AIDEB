import os
import cv2
import numpy as np
import pydicom
import tensorflow as tf
from PIL import Image
from config import Config

MODEL = None

def load_ai_model():
    global MODEL
    if MODEL is None:
        if os.path.exists(Config.MODEL_PATH):
            # Memuat model .keras milik Anda menggunakan TensorFlow
            MODEL = tf.keras.models.load_model(Config.MODEL_PATH)
            print(f"--- [SUKSES] Model AI Berhasil Dimuat dari {Config.MODEL_PATH} ---")
        else:
            print(f"--- [PERINGATAN] File model tidak ditemukan di {Config.MODEL_PATH} ---")
    return MODEL

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in Config.ALLOWED_EXTENSIONS

def is_not_medical_image(file_stream, threshold=15.0):
    # 1. Cek ekstensi file terlebih dahulu. Jika formatnya .dcm (DICOM),
    #    maka otomatis dianggap sebagai citra medis.
    filename = getattr(file_stream, 'filename', '')
    if filename and filename.rsplit('.', 1)[-1].lower() == 'dcm':
        return False

    # 2. Baca gambar dari memory stream (karena file belum disimpan)
    file_bytes = np.frombuffer(file_stream.read(), np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # 3. Reset posisi pointer file ke awal agar bisa dibaca lagi nanti
    file_stream.seek(0)
    
    if img_bgr is None:
        return True
    
    # 4. Pecah gambar menjadi 3 channel: Blue, Green, Red
    b, g, r = cv2.split(img_bgr)
    
    # 5. Hitung selisih antar channel warna
    diff_rg = np.abs(r.astype(np.int16) - g.astype(np.int16))
    diff_rb = np.abs(r.astype(np.int16) - b.astype(np.int16))
    diff_gb = np.abs(g.astype(np.int16) - b.astype(np.int16))
    
    # 6. Hitung rata-rata deviasi warna gambar
    mean_diff = (np.mean(diff_rg) + np.mean(diff_rb) + np.mean(diff_gb)) / 3.0
    
    # Jika rata-rata selisih warna di atas threshold, artinya gambar terlalu berwarna
    return mean_diff > threshold

def process_upload_validation(file):
    if file.filename == '':
        return {
            "success": False, 
            "message": "Nama file tidak boleh kosong!", 
            "status_code": 400
        }
    
    if not allowed_file(file.filename):
        return {
            "success": False, 
            "message": f"Format file tidak diizinkan! Hanya menerima format: {', '.join(Config.ALLOWED_EXTENSIONS)}", 
            "status_code": 400
        }
        
    file.seek(0, os.SEEK_END)  # Geser kursor ke ujung akhir file untuk tahu ukurannya
    file_length = file.tell()  # Ambil posisi ukuran byte terakhir
    file.seek(0)
    
    if file_length > Config.MAX_CONTENT_LENGTH:
        max_mb = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
        return {
            "success": False,
            "message": f"Ukuran file terlalu besar! Maksimal ukuran yang diizinkan adalah {max_mb} MB.",
            "status_code": 413 # 413 Payload Too Large
        }
        
    # Validasi konten gambar (memastikan citra medis grayscale)
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext != 'dcm':
        if is_not_medical_image(file):
            return {
                "success": False,
                "message": "File ditolak! Gambar terdeteksi terlalu berwarna dan tidak dikenali sebagai CT Scan/Rontgen medis.",
                "status_code": 400
            }
        
    return {"success": True, "status_code": 200}

def read_image_file(file_path):
    ext = file_path.split('.')[-1].lower()
    
    # Jika filenya adalah format rontgen medis asli (DICOM)
    if ext == 'dcm':
        ds = pydicom.dcmread(file_path)
        img_array = ds.pixel_array
        
        # Konversi ke uint8 (skala 0-255) agar bisa diolah oleh OpenCV
        img_array = ((img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array)) * 255).astype(np.uint8)
        
        # Deteksi dimensi / channel gambar DICOM secara dinamis
        if len(img_array.shape) == 2:
            # Jika 2 dimensi (Grayscale 1 channel), konversi ke RGB 3 channel
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif len(img_array.shape) == 3:
            if img_array.shape[2] == 1:
                # Jika 3 dimensi tapi channel-nya cuma 1
                img_rgb = cv2.cvtColor(img_array[:, :, 0], cv2.COLOR_GRAY2RGB)
            elif img_array.shape[2] == 3:
                # Jika sudah 3 channel, gunakan langsung
                img_rgb = img_array
            elif img_array.shape[2] == 4:
                # Jika RGBA (4 channel), buang alpha channel-nya ke RGB
                img_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            else:
                img_rgb = img_array
        else:
            img_rgb = img_array
            
        return img_rgb
    
    # Jika filenya adalah gambar standar (PNG/JPG)
    else:
        # Membaca gambar dengan OpenCV (Default: BGR)
        img_bgr = cv2.imread(file_path)
        if img_bgr is None:
            raise ValueError("Gagal membaca file gambar (file rusak atau tidak didukung)")
            
        # Deteksi dimensi / channel gambar standar secara dinamis
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
    
def preprocess_for_mobilenet(file_path, target_size=(256,256)):
    
     try:
         # 1. Baca gambar sesuai ekstensinya
         img = read_image_file(file_path)
         
         # 2. Resize gambar menjadi 256x256 sesuai bentuk input Netron [?, 256, 256, 3]
         img_resized = cv2.resize(img, target_size)
         
         # 3. Normalisasi piksel (membagi dengan 255.0) seperti rumus notebook Anda
         img_normalized = img_resized / 255.0
         img_normalized = img_normalized.astype(np.float32)
         
         # 4. Expand dimensi dari (256, 256, 3) menjadi (1, 256, 256, 3)
         # Ini dilakukan karena Keras menerima input dalam bentuk batch/kumpulan gambar
         img_final = np.expand_dims(img_normalized, axis=0)
         
         return {"success": True, "processed_data": img_final}
     
     except Exception as e:
         return {"success": False, "message": f"Gagal memproses gambar: {str(e)}",}
     
def run_ai_prediction(file_path):
    model = load_ai_model()
    if model is None:
        return {
            "success": False, 
            "message": "AI Model belum tersedia!",
            "status_code": 503
        }
    
    try:
        # 1. Lakukan preprocessing gambar
        preprocess_res = preprocess_for_mobilenet(file_path)
        if not preprocess_res["success"]:
            return {
                "success": False,
                "message": preprocess_res["message"]
            }
        
        input_data = preprocess_res["processed_data"]
        
        # 2. Prediksi menggunakan model
        prediction_probs = model.predict(input_data, verbose=0)
        
        classes = ['Normal', 'Tumor Ginjal']
        predicted_class_idx = int(np.argmax(prediction_probs[0]))
        hasil_diagnosis = classes[predicted_class_idx]
        
        confidence_score = float(prediction_probs[0][predicted_class_idx])
        
        is_doubtful = confidence_score < 0.70
        
        return {
            "success": True,
            "prediction": hasil_diagnosis,
            "confidence": confidence_score,
            "is_doubtful": is_doubtful,
            "message": "Model AI ragu-ragu. Struktur anatomi gambar tidak dikenali sebagai CT Scan Ginjal yang valid." if is_doubtful else "File gambar CT Scan berhasil dianalisis"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Terjadi eror saat analisis AI: {str(e)}"}