from config import Config

def check_login_credentials(username,password):
    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        return {
            "success": True,
            "message": "Login sukses! Selamat datang kembali.",
            "token": "dummy-jwt-token-detuji-2026"
        }
    else:
        return{
            "success": False,
            "message": "Username atau Password salah, silakan coba lagi!"
        }
