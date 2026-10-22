from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
import os
from routes.register_API import register_bp
from routes.user_login_API import login_bp
from routes.ask_AI_API import AI_bp
from routes.chat_API import chat_bp
from routes.member_API import member_bp
from routes.password_reset_API import password_reset_bp
from routes.admin_auth_API import admin_auth_bp
from routes.admin_users_API import admin_users_bp
from routes.health_content_API import health_content_bp
from routes.admin_monitoring_API import admin_monitoring_bp

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for the entire app

# Frontend directory (relative to backend/)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

@app.route('/')
def index():
    return redirect('/home.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# Register Blueprints
app.register_blueprint(register_bp)
app.register_blueprint(login_bp)
app.register_blueprint(AI_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(member_bp)
app.register_blueprint(password_reset_bp)
app.register_blueprint(admin_auth_bp)
app.register_blueprint(admin_users_bp)
app.register_blueprint(health_content_bp)
app.register_blueprint(admin_monitoring_bp)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)