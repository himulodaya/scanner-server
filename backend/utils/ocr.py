"""OCR Processing Utilities"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def process_image(image_path, output_pdf_path, ocr_config):
    """
    Process an image with OCR and create a searchable PDF

    Args:
        image_path (str): Path to the input image
        output_pdf_path (str): Path for the output PDF
        ocr_config (dict): OCR configuration options

    Returns:
        dict: Result with success status and optional error message
    """
    try:
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": f"Input image not found: {image_path}"
            }

        # Build ocrmypdf command
        cmd = [
            'ocrmypdf',
            '--language', ocr_config.get('language', 'eng'),
            '--optimize', str(ocr_config.get('optimize', 3)),
        ]

        # Add optional flags
        if ocr_config.get('deskew', True):
            cmd.append('--deskew')

        if ocr_config.get('clean', True):
            cmd.append('--clean')

        # Add force OCR flag to process images
        cmd.append('--force-ocr')

        # Add input and output paths
        cmd.extend([image_path, output_pdf_path])

        logger.info("Running OCR with command: %s", ' '.join(cmd))

        # Execute OCR command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0 and os.path.exists(output_pdf_path):
            logger.info("OCR processing completed successfully")
            return {
                "success": True,
                "output_path": output_pdf_path
            }
        else:
            logger.error("OCR failed: %s", result.stderr)
            return {
                "success": False,
                "error": "OCR processing failed",
                "stderr": result.stderr
            }

    except subprocess.TimeoutExpired:
        logger.error("OCR processing timed out")
        return {
            "success": False,
            "error": "OCR processing timed out"
        }
    except Exception as e:
        logger.exception("Error during OCR processing: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }


def make_pdf_searchable(pdf_path, ocr_config):
    """
    Make an existing PDF searchable using OCR

    Args:
        pdf_path (str): Path to the PDF file
        ocr_config (dict): OCR configuration options

    Returns:
        dict: Result with success status and optional error message
    """
    try:
        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "error": f"PDF file not found: {pdf_path}"
            }

        # Create temp output path
        temp_output = f"{pdf_path}.temp.pdf"

        # Build ocrmypdf command
        cmd = [
            'ocrmypdf',
            '--language', ocr_config.get('language', 'eng'),
            '--optimize', str(ocr_config.get('optimize', 3)),
        ]

        # Add optional flags
        if ocr_config.get('deskew', True):
            cmd.append('--deskew')

        if ocr_config.get('clean', True):
            cmd.append('--clean')

        # Skip already processed pages
        cmd.append('--skip-text')

        # Add input and output paths
        cmd.extend([pdf_path, temp_output])

        logger.info("Making PDF searchable with command: %s", ' '.join(cmd))

        # Execute OCR command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0 and os.path.exists(temp_output):
            # Replace original with OCR'd version
            os.replace(temp_output, pdf_path)
            logger.info("PDF made searchable successfully")
            return {
                "success": True,
                "output_path": pdf_path
            }
        else:
            # Clean up temp file if it exists
            if os.path.exists(temp_output):
                os.remove(temp_output)

            logger.error("Failed to make PDF searchable: %s", result.stderr)
            return {
                "success": False,
                "error": "Failed to make PDF searchable",
                "stderr": result.stderr
            }

    except subprocess.TimeoutExpired:
        logger.error("OCR processing timed out")
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return {
            "success": False,
            "error": "OCR processing timed out"
        }
    except Exception as e:
        logger.exception("Error making PDF searchable: %s", str(e))
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return {
            "success": False,
            "error": str(e)
        }
