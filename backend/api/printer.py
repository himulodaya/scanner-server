import os
import time
import subprocess
import logging
from pathlib import Path
from ..config import load_config

logger = logging.getLogger(__name__)

def get_available_printers():
    """Get list of available printers"""
    try:
        result = subprocess.run(["lpstat", "-a"], capture_output=True, text=True)
        printers = []
        
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    # Parse printer name from lpstat output
                    printer_name = line.split()[0]
                    printers.append(printer_name)
        
        return {
            "success": True,
            "printers": printers
        }
    except Exception as e:
        logger.exception("Error getting printer list: %s", str(e))
        return {
            "success": False,
            "error": str(e),
            "printers": []
        }

def print_file(file_data, printer_name):
    """Print an uploaded file"""
    config = load_config()
    storage_path = Path(config["storage"]["path"])
    temp_dir = storage_path / "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create a safe filename
    original_filename = file_data.filename
    safe_filename = "".join(c if c.isalnum() or c == '.' else '_' for c in original_filename)
    
    # Save uploaded file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    file_path = temp_dir / f"print_{timestamp}_{safe_filename}"
    
    try:
        # Save the file
        file_data.save(str(file_path))
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "Failed to save uploaded file"
            }
        
        # Print the file
        print_cmd = f"lp -d {printer_name} \"{file_path}\""
        logger.info("Printing file with command: %s", print_cmd)
        
        result = subprocess.run(print_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error("Print failed: %s", result.stderr)
            return {
                "success": False,
                "error": f"Print failed: {result.stderr}",
                "file_path": str(file_path)
            }
        
        return {
            "success": True,
            "file_path": str(file_path),
            "original_filename": original_filename,
            "printer": printer_name,
            "output": result.stdout
        }
    
    except Exception as e:
        logger.exception("Error printing file: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }
