"""Tests for utility functions"""
import os
import pytest
from pathlib import Path
from backend.utils import pdf, ocr, notifications


class TestPDFUtils:
    """Test PDF utility functions"""

    def test_pdf_module_import(self):
        """Test that PDF module can be imported"""
        assert hasattr(pdf, 'convert_image_to_pdf')
        assert hasattr(pdf, 'combine_images_to_pdf')
        assert hasattr(pdf, 'merge_pdfs')

    def test_convert_nonexistent_image(self):
        """Test converting non-existent image returns error"""
        result = pdf.convert_image_to_pdf(
            '/nonexistent/image.jpg',
            '/tmp/output.pdf'
        )
        assert result['success'] is False
        assert 'error' in result

    def test_combine_empty_images_list(self):
        """Test combining empty list of images returns error"""
        result = pdf.combine_images_to_pdf([], '/tmp/output.pdf')
        assert result['success'] is False
        assert 'error' in result


class TestOCRUtils:
    """Test OCR utility functions"""

    def test_ocr_module_import(self):
        """Test that OCR module can be imported"""
        assert hasattr(ocr, 'process_image')
        assert hasattr(ocr, 'make_pdf_searchable')

    def test_process_nonexistent_image(self):
        """Test processing non-existent image returns error"""
        ocr_config = {
            'language': 'eng',
            'optimize': 3,
            'deskew': True,
            'clean': True
        }
        result = ocr.process_image(
            '/nonexistent/image.jpg',
            '/tmp/output.pdf',
            ocr_config
        )
        assert result['success'] is False
        assert 'error' in result


class TestNotifications:
    """Test notification utilities"""

    def test_notifications_module_import(self):
        """Test that notifications module can be imported"""
        assert hasattr(notifications, 'send_to_discord')
        assert hasattr(notifications, 'test_discord_webhook')

    def test_test_webhook_empty_url(self):
        """Test webhook with empty URL returns error"""
        result = notifications.test_discord_webhook('')
        assert result['success'] is False
        assert 'error' in result

    def test_send_discord_empty_webhook(self):
        """Test sending to empty webhook returns False"""
        result = notifications.send_to_discord(
            '/tmp/test.pdf',
            'Test message',
            ''
        )
        assert result is False
