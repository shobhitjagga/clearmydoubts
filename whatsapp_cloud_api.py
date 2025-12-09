"""
WhatsApp Cloud API integration (original implementation)
Preserved for backward compatibility
"""
import requests
import os

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


def send_whatsapp_message(to, message):
    """
    Send message via WhatsApp Cloud API.
    WhatsApp text body must be <= 4096 chars. Split long replies into chunks.
    """
    if message is None:
        print("No message to send")
        return

    if not WHATSAPP_TOKEN or not PHONE_ID:
        print("WhatsApp Cloud API credentials not configured")
        return

    text = str(message)
    max_len = 4000  # keep a buffer under 4096
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)] or [text]

    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    for idx, part in enumerate(chunks, start=1):
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {"body": part}
        }
        response = requests.post(url, json=data, headers=headers)
        try:
            resp_json = response.json()
        except Exception:
            resp_json = {"error": "failed to parse response", "status": response.status_code}

        print(f"WhatsApp Cloud API response (chunk {idx}/{len(chunks)}):", resp_json)

        # If the API returns an error, stop sending remaining chunks to avoid spam
        if response.status_code >= 400:
            break


def get_media_url(media_id):
    """
    Get media URL from WhatsApp Cloud API using media ID.
    """
    if not WHATSAPP_TOKEN:
        raise ValueError("WhatsApp Cloud API token not configured")
    
    media_url = f"https://graph.facebook.com/v20.0/{media_id}"
    media_resp = requests.get(
        media_url,
        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    )
    media_resp.raise_for_status()
    media_data = media_resp.json()
    return media_data["url"]


def download_media(file_url):
    """
    Download media file from WhatsApp Cloud API.
    """
    if not WHATSAPP_TOKEN:
        raise ValueError("WhatsApp Cloud API token not configured")
    
    img_resp = requests.get(
        file_url,
        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    )
    img_resp.raise_for_status()
    return img_resp.content

