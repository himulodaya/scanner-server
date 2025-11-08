"""PDF Manipulation Utilities"""
import os
import subprocess
import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


def convert_image_to_pdf(image_path, pdf_path):
    """
    Convert an image file to PDF format

    Args:
        image_path (str): Path to the input image
        pdf_path (str): Path for the output PDF

    Returns:
        dict: Result with success status
    """
    try:
        if not os.path.exists(image_path):
            logger.error("Input image not found: %s", image_path)
            return {
                "success": False,
                "error": f"Input image not found: {image_path}"
            }

        # Use Pillow to convert image to PDF
        logger.info("Converting image %s to PDF %s", image_path, pdf_path)

        # Open and convert image
        image = Image.open(image_path)

        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # Save as PDF
        image.save(pdf_path, 'PDF', resolution=100.0)

        logger.info("Image converted to PDF successfully")
        return {
            "success": True,
            "output_path": pdf_path
        }

    except Exception as e:
        logger.exception("Error converting image to PDF: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }


def combine_images_to_pdf(image_paths, output_pdf_path):
    """
    Combine multiple images into a single PDF

    Args:
        image_paths (list): List of image file paths
        output_pdf_path (str): Path for the output PDF

    Returns:
        dict: Result with success status
    """
    try:
        if not image_paths:
            return {
                "success": False,
                "error": "No images provided"
            }

        # Verify all images exist
        for img_path in image_paths:
            if not os.path.exists(img_path):
                return {
                    "success": False,
                    "error": f"Image not found: {img_path}"
                }

        logger.info("Combining %d images into PDF %s", len(image_paths), output_pdf_path)

        # Open all images
        images = []
        for img_path in image_paths:
            img = Image.open(img_path)

            # Convert to RGB if necessary
            if img.mode == 'RGBA':
                rgb_image = Image.new('RGB', img.size, (255, 255, 255))
                rgb_image.paste(img, mask=img.split()[3])
                img = rgb_image
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            images.append(img)

        # Save the first image as PDF with remaining images appended
        if len(images) == 1:
            images[0].save(output_pdf_path, 'PDF', resolution=100.0)
        else:
            images[0].save(
                output_pdf_path,
                'PDF',
                resolution=100.0,
                save_all=True,
                append_images=images[1:]
            )

        # Close all images
        for img in images:
            img.close()

        logger.info("Successfully combined %d images into PDF", len(image_paths))
        return {
            "success": True,
            "output_path": output_pdf_path,
            "page_count": len(image_paths)
        }

    except Exception as e:
        logger.exception("Error combining images to PDF: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }


def merge_pdfs(pdf_paths, output_pdf_path):
    """
    Merge multiple PDF files into one

    Args:
        pdf_paths (list): List of PDF file paths
        output_pdf_path (str): Path for the output PDF

    Returns:
        dict: Result with success status
    """
    try:
        if not pdf_paths:
            return {
                "success": False,
                "error": "No PDFs provided"
            }

        # Verify all PDFs exist
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                return {
                    "success": False,
                    "error": f"PDF not found: {pdf_path}"
                }

        logger.info("Merging %d PDFs into %s", len(pdf_paths), output_pdf_path)

        # Use pdftk to merge PDFs
        cmd = ['pdftk'] + pdf_paths + ['cat', 'output', output_pdf_path]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and os.path.exists(output_pdf_path):
            logger.info("Successfully merged %d PDFs", len(pdf_paths))
            return {
                "success": True,
                "output_path": output_pdf_path,
                "pdf_count": len(pdf_paths)
            }
        else:
            logger.error("PDF merge failed: %s", result.stderr)
            return {
                "success": False,
                "error": "PDF merge failed",
                "stderr": result.stderr
            }

    except subprocess.TimeoutExpired:
        logger.error("PDF merge timed out")
        return {
            "success": False,
            "error": "PDF merge timed out"
        }
    except Exception as e:
        logger.exception("Error merging PDFs: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }
