import logging
from ..config import load_config, update_config, save_config
from ..auth import test_oauth_config

logger = logging.getLogger(__name__)

def get_settings():
    """Get current settings"""
    try:
        config = load_config()
        return {
            "success": True,
            "config": config
        }
    except Exception as e:
        logger.exception("Error getting settings: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }

def update_settings(updated_settings):
    """Update settings with new values"""
    try:
        result = update_config(updated_settings)
        return {
            "success": result,
            "message": "Settings updated successfully" if result else "Failed to update settings"
        }
    except Exception as e:
        logger.exception("Error updating settings: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }

def test_scanner_connection(scanner_settings):
    """Test scanner connection with provided settings"""
    import subprocess
    
    scanner_ip = scanner_settings.get("ip", "192.168.1.100")
    scanner_protocol = scanner_settings.get("protocol", "escl")
    scanner_port = scanner_settings.get("port", 443)
    
    try:
        # Test if scanner is reachable
        ping_cmd = f"ping -c 1 -W 2 {scanner_ip}"
        ping_result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True)
        
        ping_success = ping_result.returncode == 0
        
        # Test scanner connection with appropriate command
        if scanner_protocol == "escl":
            scan_cmd = f"scanimage -d escl:https://{scanner_ip}:{scanner_port} -n --resolution=75"
        else:
            scan_cmd = f"scanimage -d hpaio:/net/DeskJet_2700_series?ip={scanner_ip} -n --resolution=75"
        
        scan_result = subprocess.run(scan_cmd, shell=True, capture_output=True, text=True)
        scan_success = scan_result.returncode == 0
        
        return {
            "success": ping_success and scan_success,
            "ping_success": ping_success,
            "scanner_success": scan_success,
            "details": {
                "ping_output": ping_result.stdout if ping_success else ping_result.stderr,
                "scanner_output": scan_result.stdout if scan_success else scan_result.stderr
            }
        }
    except Exception as e:
        logger.exception("Error testing scanner connection: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }

def test_discord_webhook(webhook_url):
    """Test Discord webhook by sending a test message"""
    try:
        import requests
        import json

        payload = {
            "content": "This is a test message from Scanner Server.",
            "username": "Scanner Server Test"
        }

        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        return {
            "success": response.status_code == 204,
            "status_code": response.status_code,
            "response": response.text
        }
    except Exception as e:
        logger.exception("Error testing Discord webhook: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }

def test_oauth(oauth_settings):
    """Test OAuth configuration"""
    return test_oauth_config(oauth_settings)
