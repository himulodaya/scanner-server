import os
import time
import subprocess
import logging
from pathlib import Path
from ..utils import ocr, pdf
from ..config import load_config

logger = logging.getLogger(__name__)

def scan_single_page():
    """Scan a single page and process it"""
    config = load_config()
    scanner_config = config["scanner"]
    storage_config = config["storage"]
    
    # Create timestamp and file paths
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    storage_path = Path(storage_config["path"])
    temp_dir = storage_path / "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create output file paths
    output_img = temp_dir / f"scan_{timestamp}.jpg"
    output_pdf = storage_path / f"scan_{timestamp}.pdf"
    
    # Build scan command
    scanner_ip = scanner_config["ip"]
    scanner_protocol = scanner_config["protocol"]
    scanner_port = scanner_config.get("port", 443)
    scanner_mode = scanner_config.get("mode", "color")
    scanner_resolution = scanner_config.get("resolution", 300)
    
    # Construct the scan command based on protocol
    if scanner_protocol == "escl":
        scan_cmd = f"hp-scan --device=escl:https://{scanner_ip}:{scanner_port} --mode={scanner_mode} --resolution={scanner_resolution} --output={output_img}"
    else:
        # Default to hpaio
        scan_cmd = f"hp-scan --device=hpaio:/net/DeskJet_2700_series?ip={scanner_ip} --mode={scanner_mode} --resolution={scanner_resolution} --output={output_img}"
    
    try:
        # Execute scan command
        logger.info("Scanning document with command: %s", scan_cmd)
        result = subprocess.run(scan_cmd, shell=True, capture_output=True, text=True)
        
        if not os.path.exists(output_img):
            logger.error("Scan failed: %s", result.stderr)
            return {
                "success": False,
                "error": "Scan failed",
                "details": {
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            }
        
        # Process the image with OCR
        if config["ocr"]["enabled"]:
            logger.info("Performing OCR on scanned image")
            ocr_result = ocr.process_image(
                str(output_img), 
                str(output_pdf),
                config["ocr"]
            )
            
            if ocr_result["success"]:
                pdf_type = "Searchable PDF"
            else:
                # Fall back to simple conversion
                logger.warning("OCR failed, falling back to image conversion")
                pdf.convert_image_to_pdf(str(output_img), str(output_pdf))
                pdf_type = "PDF (OCR failed)"
        else:
            # Just convert to PDF without OCR
            pdf.convert_image_to_pdf(str(output_img), str(output_pdf))
            pdf_type = "PDF"
        
        # Send to Discord if enabled
        discord_notification = False
        if config["discord"]["enabled"] and config["discord"]["webhook_url"]:
            from ..utils.notifications import send_to_discord
            discord_notification = send_to_discord(
                str(output_pdf),
                "New scan",
                config["discord"]["webhook_url"]
            )
        
        # Clean up temp file
        if os.path.exists(output_img):
            os.remove(output_img)
        
        return {
            "success": True,
            "file_path": str(output_pdf),
            "file_type": pdf_type,
            "discord_notification": discord_notification
        }
        
    except Exception as e:
        logger.exception("Error during scanning: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }

# Additional functions for multi-page scanning
def start_multi_page_session():
    """Start a new multi-page scanning session"""
    config = load_config()
    storage_path = Path(config["storage"]["path"])
    temp_dir = storage_path / "temp"
    
    # Create timestamp and session directory
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = temp_dir / f"session_{timestamp}"
    os.makedirs(session_dir, exist_ok=True)
    
    return {
        "success": True,
        "session_id": timestamp,
        "session_dir": str(session_dir)
    }

def scan_page_for_session(session_id):
    """Scan a single page for an existing session"""
    config = load_config()
    scanner_config = config["scanner"]
    storage_path = Path(config["storage"]["path"])
    temp_dir = storage_path / "temp"
    session_dir = temp_dir / f"session_{session_id}"
    
    if not os.path.exists(session_dir):
        return {
            "success": False,
            "error": "Session not found"
        }
    
    # Get current page count
    existing_pages = list(session_dir.glob("page_*.jpg"))
    page_num = len(existing_pages) + 1
    
    # Create output file path
    page_img = session_dir / f"page_{page_num:03d}.jpg"
    
    # Build scan command
    scanner_ip = scanner_config["ip"]
    scanner_protocol = scanner_config["protocol"]
    scanner_port = scanner_config.get("port", 443)
    scanner_mode = scanner_config.get("mode", "color")
    scanner_resolution = scanner_config.get("resolution", 300)
    
    # Construct the scan command based on protocol
    if scanner_protocol == "escl":
        scan_cmd = f"hp-scan --device=escl:https://{scanner_ip}:{scanner_port} --mode={scanner_mode} --resolution={scanner_resolution} --output={page_img}"
    else:
        # Default to hpaio
        scan_cmd = f"hp-scan --device=hpaio:/net/DeskJet_2700_series?ip={scanner_ip} --mode={scanner_mode} --resolution={scanner_resolution} --output={page_img}"
    
    try:
        # Execute scan command
        logger.info("Scanning page %d for session %s", page_num, session_id)
        result = subprocess.run(scan_cmd, shell=True, capture_output=True, text=True)
        
        if not os.path.exists(page_img):
            logger.error("Scan failed: %s", result.stderr)
            return {
                "success": False,
                "error": "Scan failed",
                "details": {
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            }
        
        # Get updated page list
        updated_pages = sorted(list(session_dir.glob("page_*.jpg")))
        
        return {
            "success": True,
            "page_number": page_num,
            "total_pages": len(updated_pages),
            "page_path": str(page_img)
        }
        
    except Exception as e:
        logger.exception("Error during page scanning: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }

def finish_multi_page_session(session_id):
    """Finalize a multi-page scanning session"""
    config = load_config()
    storage_path = Path(config["storage"]["path"])
    temp_dir = storage_path / "temp"
    session_dir = temp_dir / f"session_{session_id}"
    
    if not os.path.exists(session_dir):
        return {
            "success": False,
            "error": "Session not found"
        }
    
    # Get all pages
    pages = sorted(list(session_dir.glob("page_*.jpg")))
    if not pages:
        return {
            "success": False,
            "error": "No pages found in session"
        }
    
    # Create output filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_pdf = storage_path / f"multi_page_{timestamp}.pdf"
    
    try:
        # Process based on number of pages
        if len(pages) == 1:
            # Single page - use OCR directly
            if config["ocr"]["enabled"]:
                ocr_result = ocr.process_image(
                    str(pages[0]), 
                    str(output_pdf),
                    config["ocr"]
                )
                pdf_type = "Searchable PDF" if ocr_result["success"] else "PDF (OCR failed)"
            else:
                pdf.convert_image_to_pdf(str(pages[0]), str(output_pdf))
                pdf_type = "PDF"
        else:
            # Multiple pages - combine then OCR
            result = pdf.combine_images_to_pdf([str(p) for p in pages], str(output_pdf))
            
            if result["success"] and config["ocr"]["enabled"]:
                # Make the PDF searchable
                ocr_result = ocr.make_pdf_searchable(
                    str(output_pdf),
                    config["ocr"]
                )
                pdf_type = "Searchable PDF" if ocr_result["success"] else "PDF (not searchable)"
            else:
                pdf_type = "PDF"
        
        # Send to Discord if enabled
        discord_notification = False
        if config["discord"]["enabled"] and config["discord"]["webhook_url"]:
            from ..utils.notifications import send_to_discord
            discord_notification = send_to_discord(
                str(output_pdf),
                f"New multi-page scan ({len(pages)} pages)",
                config["discord"]["webhook_url"]
            )
        
        # Clean up session directory
        import shutil
        shutil.rmtree(session_dir)
        
        return {
            "success": True,
            "file_path": str(output_pdf),
            "file_type": pdf_type,
            "page_count": len(pages),
            "discord_notification": discord_notification
        }
        
    except Exception as e:
        logger.exception("Error finalizing multi-page scan: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }
