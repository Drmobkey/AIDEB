import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password')

    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}
    MODEL_PATH = 'model_storage/best_model_mobilenet256try2.h5'
    
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024
