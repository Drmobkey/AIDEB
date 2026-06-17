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
    
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    # Memperbaiki pembuatan folder untuk model path
    os.makedirs(os.path.dirname(Config.MODEL_PATH), exist_ok=True)
    
    
    # Memicu pemuatan model .h5 ke memori RAM saat server dihidupkan
    with app.app_context():
        load_ai_model()
        
    
    # Blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(pdf_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5002, debug=True)
