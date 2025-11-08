import os
import logging
import sys
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
from .config import load_config
from .api import scanner, printer, settings
from . import auth

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__,
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

# Security configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))

# Rate limiting to prevent abuse
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Load configuration
config = load_config()

# Initialize OAuth authentication
auth.init_oauth(app)

logger.info("Scanner Server starting up...")
logger.info(f"Configuration loaded from: {os.getenv('CONFIG_DIR', './config')}")

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
@auth.auth_required
def download_file(filename):
    """Download scanned files"""
    try:
        config = load_config()
        storage_path = config["storage"]["path"]

        # Security: Prevent directory traversal
        safe_filename = secure_filename(filename)
        if not safe_filename or safe_filename != filename:
            logger.warning(f"Attempted directory traversal with filename: {filename}")
            return jsonify({"error": "Invalid filename"}), 400

        return send_from_directory(storage_path, safe_filename)
    except Exception as e:
        logger.exception(f"Error downloading file: {str(e)}")
        return jsonify({"error": "File not found"}), 404

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    """Handle bad request errors"""
    logger.warning(f"Bad request: {str(e)}")
    return jsonify({"error": "Bad request", "message": str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    """Handle not found errors"""
    return jsonify({"error": "Not found", "message": str(e)}), 404

@app.errorhandler(413)
def request_entity_too_large(e):
    """Handle file too large errors"""
    logger.warning("File upload too large")
    return jsonify({"error": "File too large", "message": "Maximum file size is 50MB"}), 413

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors"""
    logger.warning(f"Rate limit exceeded: {get_remote_address()}")
    return jsonify({"error": "Rate limit exceeded", "message": str(e.description)}), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.exception(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all uncaught exceptions"""
    # Pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # Log the error
    logger.exception(f"Unhandled exception: {str(e)}")

    # Return JSON error for API requests
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500

    # Return error page for web requests
    return render_template('error.html', error="An unexpected error occurred"), 500

# Health check endpoint
@app.route('/health')
@limiter.exempt
def health_check():
    """Health check endpoint for Docker/monitoring"""
    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": None
    }), 200

# Main entry point
if __name__ == '__main__':
    # Ensure directories exist
    storage_path = config["storage"]["path"]
    os.makedirs(storage_path, exist_ok=True)
    os.makedirs(os.path.join(storage_path, "temp"), exist_ok=True)

    # Check debug mode from environment
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'

    if debug_mode:
        logger.warning("Running in DEBUG mode - DO NOT use in production!")
    else:
        logger.info("Running in production mode")

    # Start the app
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
