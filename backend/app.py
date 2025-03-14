import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from .config import load_config
from .api import scanner, printer, settings

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

# Create routes
@app.route('/')
def index():
    return render_template('index.html')

# Scanner API endpoints
@app.route('/api/scan/single', methods=['GET'])
def api_scan_single():
    result = scanner.scan_single_page()
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)
    
    if result["success"]:
        return render_template('scan_complete.html', result=result)
    else:
        return render_template('scan_error.html', error=result["error"])

@app.route('/api/scan/start_multi', methods=['GET'])
def api_start_multi():
    result = scanner.start_multi_page_session()
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)
    
    if result["success"]:
        return render_template('scan_multi.html', session_id=result["session_id"])
    else:
        return render_template('scan_error.html', error=result["error"])

@app.route('/api/scan/page/<session_id>', methods=['GET'])
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
def api_printer_list():
    result = printer.get_available_printers()
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)
    
    return result

@app.route('/api/printer/print', methods=['POST'])
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
def api_get_settings():
    result = settings.get_settings()
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)
    
    if result["success"]:
        return render_template('settings.html', config=result["config"])
    else:
        return render_template('settings_error.html', error=result["error"])

@app.route('/api/settings/update', methods=['POST'])
def api_update_settings():
    updated_settings = request.json
    result = settings.update_settings(updated_settings)
    return jsonify(result)

@app.route('/api/settings/test_scanner', methods=['POST'])
def api_test_scanner():
    scanner_settings = request.json
    result = settings.test_scanner_connection(scanner_settings)
    return jsonify(result)

@app.route('/api/settings/test_discord', methods=['POST'])
def api_test_discord():
    webhook_url = request.json.get('webhook_url', '')
    result = settings.test_discord_webhook(webhook_url)
    return jsonify(result)

# NFC endpoints
@app.route('/nfc/single_scan')
def nfc_single_scan():
    """Endpoint for NFC-triggered single page scan"""
    return redirect(url_for('api_scan_single'))

@app.route('/nfc/multi_scan')
def nfc_multi_scan():
    """Endpoint for NFC-triggered multi-page scan"""
    return redirect(url_for('api_start_multi'))

# Files download
@app.route('/files/<path:filename>')
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
