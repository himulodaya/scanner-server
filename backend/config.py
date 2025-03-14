import json
import os
import logging

logger = logging.getLogger(__name__)

CONFIG_DIR = os.environ.get("CONFIG_DIR", "/app/config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "default_config.json")

# Default configuration
DEFAULT_CONFIG = {
    "scanner": {
        "ip": "192.168.1.100",
        "protocol": "escl",
        "port": 443,
        "resolution": 300,
        "mode": "color"
    },
    "storage": {
        "path": "/data/scan",
        "categories": ["invoices", "receipts", "letters", "misc"]
    },
    "ocr": {
        "enabled": True,
        "language": "eng",
        "deskew": True,
        "clean": True
    },
    "discord": {
        "webhook_url": "",
        "enabled": False
    }
}

def ensure_config_dir():
    """Ensure config directory exists"""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config():
    """Load configuration from file or use defaults"""
    ensure_config_dir()
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                logger.info("Configuration loaded from %s", CONFIG_PATH)
                return config
        except Exception as e:
            logger.error("Failed to load config: %s", str(e))
    
    # Load defaults if no config exists or loading failed
    try:
        if os.path.exists(DEFAULT_CONFIG_PATH):
            with open(DEFAULT_CONFIG_PATH, 'r') as f:
                default_config = json.load(f)
        else:
            default_config = DEFAULT_CONFIG
            # Save default config to file
            with open(DEFAULT_CONFIG_PATH, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            
        # Save defaults to config file
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        logger.info("Default configuration created at %s", CONFIG_PATH)
        return default_config
    except Exception as e:
        logger.error("Failed to create default config: %s", str(e))
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    ensure_config_dir()
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("Configuration saved to %s", CONFIG_PATH)
        return True
    except Exception as e:
        logger.error("Failed to save config: %s", str(e))
        return False

def update_config(updates):
    """Update configuration with new values"""
    config = load_config()
    
    # Recursively update nested dictionaries
    def update_dict(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = update_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    updated_config = update_dict(config, updates)
    return save_config(updated_config)
