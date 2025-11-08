import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from flask_login import current_user
from werkzeug.utils import secure_filename
from .config import load_config
from .api import scanner, printer, settings
from . import auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__,
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

# Load configuration
config = load_config()

# Initialize OAuth authentication
auth.init_oauth(app)

# Create routes
@app.route('/')
@auth.auth_required
def index():
    return render_template('index.html', user=current_user if current_user.is_authenticated else None)

# Scanner API endpoints
@app.route('/api/scan/single', methods=['GET'])
@auth.auth_required
def api_scan_single():
    result = scanner.scan_single_page()
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)

    if result["success"]:
        return render_template('scan_complete.html', result=result)
    else:
        return render_template('scan_error.html', error=result["error"])

@app.route('/api/scan/start_multi', methods=['GET'])
@auth.auth_required
def api_start_multi():
    result = scanner.start_multi_page_session()
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)

    if result["success"]:
        return render_template('scan_multi.html', session_id=result["session_id"])
    else:
        return render_template('scan_error.html', error=result["error"])

@app.route('/api/scan/page/<session_id>', methods=['GET'])
@auth.auth_required
def api_scan_page(session_id):
    result = scanner.scan_page_for_session(session_id)
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)

    if result["success"]:
        return render_template('scan_page.html',
                              session_id=session_id,
                              page_num=result["page_number"],
                              total_pages=result["total_pages"])
    else:
        return render_template('scan_error.html', error=result["error"])

@app.route('/api/scan/finish/<session_id>', methods=['GET'])
@auth.auth_required
def api_finish_multi(session_id):
    result = scanner.finish_multi_page_session(session_id)
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)

    if result["success"]:
        return render_template('scan_complete.html', result=result)
    else:
        return render_template('scan_error.html', error=result["error"])

# Printer API endpoints
@app.route('/api/printer/list', methods=['GET'])
@auth.auth_required
def api_printer_list():
    result = printer.get_available_printers()
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)

    return result

@app.route('/api/printer/print', methods=['POST'])
@auth.auth_required
def api_print_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})

    printer_name = request.form.get('printer', '')
    if not printer_name:
        return jsonify({"success": False, "error": "No printer selected"})

    result = printer.print_file(file, printer_name)
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)

    if result["success"]:
        return render_template('print_complete.html', result=result)
    else:
        return render_template('print_error.html', error=result["error"])

# Settings API endpoints
@app.route('/api/settings', methods=['GET'])
@auth.auth_required
def api_get_settings():
    result = settings.get_settings()
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)

    if result["success"]:
        return render_template('settings.html', config=result["config"])
    else:
        return render_template('settings_error.html', error=result["error"])

@app.route('/api/settings/update', methods=['POST'])
@auth.auth_required
def api_update_settings():
    updated_settings = request.json
    result = settings.update_settings(updated_settings)
    return jsonify(result)

@app.route('/api/settings/test_scanner', methods=['POST'])
@auth.auth_required
def api_test_scanner():
    scanner_settings = request.json
    result = settings.test_scanner_connection(scanner_settings)
    return jsonify(result)

@app.route('/api/settings/test_discord', methods=['POST'])
@auth.auth_required
def api_test_discord():
    webhook_url = request.json.get('webhook_url', '')
    result = settings.test_discord_webhook(webhook_url)
    return jsonify(result)

@app.route('/api/settings/test_oauth', methods=['POST'])
@auth.auth_required
def api_test_oauth():
    oauth_settings = request.json
    result = settings.test_oauth(oauth_settings)
    return jsonify(result)

# OAuth authentication routes
@app.route('/auth/login')
def auth_login():
    """Initiate OAuth login"""
    return auth.login()

@app.route('/auth/callback')
def auth_callback():
    """OAuth callback handler"""
    return auth.callback()

@app.route('/auth/logout')
def auth_logout():
    """Logout user"""
    return auth.logout_user_route()

# NFC endpoints
@app.route('/nfc/single_scan')
@auth.auth_required
def nfc_single_scan():
    """Endpoint for NFC-triggered single page scan"""
    return redirect(url_for('api_scan_single'))

@app.route('/nfc/multi_scan')
@auth.auth_required
def nfc_multi_scan():
    """Endpoint for NFC-triggered multi-page scan"""
    return redirect(url_for('api_start_multi'))

# Files download
@app.route('/files/<path:filename>')
@auth.auth_required
def download_file(filename):
    """Download scanned files"""
    config = load_config()
    storage_path = config["storage"]["path"]
    return send_from_directory(storage_path, filename)

# Main entry point
if __name__ == '__main__':
    # Ensure directories exist
    storage_path = config["storage"]["path"]
    os.makedirs(storage_path, exist_ok=True)
    os.makedirs(os.path.join(storage_path, "temp"), exist_ok=True)
    
    # Start the app
    app.run(host='0.0.0.0', port=5000, debug=True)
