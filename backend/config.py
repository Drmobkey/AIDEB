import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password')

    UPLOAD_FOLDER = 'uploads'
    # Format yang diterima: gambar standar + DICOM (format MRI/CT scan medis)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}
    # Path ke model YOLOv8n-cls untuk deteksi epilepsi
    MODEL_PATH = 'model_storage/best.pt'

    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB

    # Ambang batas toleransi warna untuk membedakan citra medis (grayscale) dengan gambar biasa.
    # Semakin rendah nilainya, semakin ketat sistem menolak gambar berwarna.
    COLOR_THRESHOLD = 10.0

    # Ambang batas kecerahan sudut gambar (khas MRI otak berlatar hitam pekat di setiap sudut)
    MRI_CORNER_THRESHOLD = 50.0

    # Ambang batas kecerahan tengah gambar (memastikan ada objek otak di tengah, bukan kosong)
    MRI_CENTER_THRESHOLD = 15.0

