import os
import sys

# Ensure backend directory is in sys.path regardless of working directory
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from flask import Flask, send_from_directory, redirect, jsonify
from flask_cors import CORS
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

@app.route('/api/status')
@app.route('/health')
@app.route('/system/status')
def system_health_status():
    return jsonify({"status": "healthy", "service": "Niramaya Health AI", "online": True}), 200

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

# Automatic database setup in background (does not block gunicorn worker boot)
def _background_db_init():
    try:
        from init_db import setup_database
        setup_database()
    except Exception as _e:
        print(f"Database auto-setup notice: {_e}")

import threading
threading.Thread(target=_background_db_init, daemon=True).start()

if __name__ == "__main__":
    import sys
    # Get the site-packages directory to exclude from watchdog reloader
    site_packages = None
    for p in sys.path:
        if 'site-packages' in p:
            site_packages = p
            break
    
    exclude = []
    if site_packages:
        exclude.append(site_packages.replace('\\', '/') + '/*')
    
    run_port = int(os.environ.get("PORT", 5000))
    app.run(
        debug=False,
        host='0.0.0.0',
        port=run_port
    )