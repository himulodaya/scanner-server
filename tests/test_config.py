"""Tests for configuration management"""
import os
import json
import pytest
from backend.config import load_config


def test_load_default_config():
    """Test loading default configuration"""
    config = load_config()

    # Check main sections exist
    assert 'scanner' in config
    assert 'storage' in config
    assert 'ocr' in config
    assert 'discord' in config

    # Check scanner defaults
    assert 'ip' in config['scanner']
    assert 'protocol' in config['scanner']
    assert 'resolution' in config['scanner']

    # Check storage defaults
    assert 'path' in config['storage']
    assert 'categories' in config['storage']


def test_scanner_config_structure():
    """Test scanner configuration structure"""
    config = load_config()

    assert config['scanner']['protocol'] in ['escl', 'hpaio']
    assert isinstance(config['scanner']['port'], int)
    assert isinstance(config['scanner']['resolution'], int)


def test_ocr_config_structure():
    """Test OCR configuration structure"""
    config = load_config()

    assert isinstance(config['ocr']['enabled'], bool)
    assert 'language' in config['ocr']
    assert isinstance(config['ocr']['optimize'], int)


def test_storage_categories():
    """Test storage categories configuration"""
    config = load_config()

    categories = config['storage']['categories']
    assert isinstance(categories, list)
    assert len(categories) > 0
