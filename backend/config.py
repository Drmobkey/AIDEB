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
    MODEL_PATH = 'model_storage/yolotry.pt'

    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB
