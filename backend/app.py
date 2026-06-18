import os
from flask import Flask
from flask_cors import CORS
from config import Config
from routes.auth_routes import auth_bp
from routes.predict_routes import predict_bp
from routes.pdf_routes import pdf_bp
from services.ai_service import load_ai_model

def create_app():
    app = Flask(__name__)

    CORS(app)

    app.config.from_object(Config)

    # Pastikan folder uploads tersedia
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Pastikan folder model_storage tersedia
    model_dir = os.path.dirname(Config.MODEL_PATH)
    if model_dir:
        os.makedirs(model_dir, exist_ok=True)

    # Muat model YOLOv8 AIDEB ke memori saat server pertama kali dihidupkan
    with app.app_context():
        load_ai_model()

    # Daftarkan Blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(pdf_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True)

