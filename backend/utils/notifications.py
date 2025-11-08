"""Notification Utilities for Discord Integration"""
import os
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


def send_to_discord(file_path, message, webhook_url, include_file=True):
    """
    Send a notification to Discord with optional file attachment

    Args:
        file_path (str): Path to the file to attach
        message (str): Message to send with the notification
        webhook_url (str): Discord webhook URL
        include_file (bool): Whether to include the file as an attachment

    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False

        logger.info("Sending Discord notification: %s", message)

        # Prepare the message payload
        data = {
            "content": message,
            "username": "Scanner Server"
        }

        # Send with or without file attachment
        if include_file and os.path.exists(file_path):
            file_name = Path(file_path).name

            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, 'application/pdf')
                }

                response = requests.post(
                    webhook_url,
                    data=data,
                    files=files,
                    timeout=30
                )
        else:
            # Send message only (no file)
            response = requests.post(
                webhook_url,
                json=data,
                timeout=30
            )

        if response.status_code in (200, 204):
            logger.info("Discord notification sent successfully")
            return True
        else:
            logger.error("Discord notification failed: %s - %s",
                        response.status_code, response.text)
            return False

    except requests.exceptions.Timeout:
        logger.error("Discord notification timed out")
        return False
    except requests.exceptions.RequestException as e:
        logger.error("Discord notification request failed: %s", str(e))
        return False
    except Exception as e:
        logger.exception("Error sending Discord notification: %s", str(e))
        return False


def test_discord_webhook(webhook_url):
    """
    Test a Discord webhook URL

    Args:
        webhook_url (str): Discord webhook URL to test

    Returns:
        dict: Result with success status and optional error message
    """
    try:
        if not webhook_url:
            return {
                "success": False,
                "error": "Webhook URL is empty"
            }

        logger.info("Testing Discord webhook")

        # Send a test message
        data = {
            "content": "🔔 Test notification from Scanner Server",
            "username": "Scanner Server"
        }

        response = requests.post(
            webhook_url,
            json=data,
            timeout=10
        )

        if response.status_code in (200, 204):
            logger.info("Discord webhook test successful")
            return {
                "success": True,
                "message": "Test notification sent successfully"
            }
        else:
            logger.error("Discord webhook test failed: %s", response.text)
            return {
                "success": False,
                "error": f"Webhook returned status {response.status_code}",
                "details": response.text
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        logger.exception("Error testing Discord webhook: %s", str(e))
        return {
            "success": False,
            "error": str(e)
        }


def send_embed_to_discord(webhook_url, title, description, color=0x00ff00, fields=None):
    """
    Send a rich embed message to Discord

    Args:
        webhook_url (str): Discord webhook URL
        title (str): Embed title
        description (str): Embed description
        color (int): Embed color (hex integer)
        fields (list): List of field dicts with 'name', 'value', 'inline' keys

    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": None
        }

        if fields:
            embed["fields"] = fields

        data = {
            "username": "Scanner Server",
            "embeds": [embed]
        }

        response = requests.post(
            webhook_url,
            json=data,
            timeout=10
        )

        return response.status_code in (200, 204)

    except Exception as e:
        logger.exception("Error sending Discord embed: %s", str(e))
        return False
