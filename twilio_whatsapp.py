"""
Twilio WhatsApp integration
"""
import os
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")  # Format: whatsapp:+14155238886

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_whatsapp_message(to, message):
    """
    Send message via Twilio WhatsApp API.
    Twilio messages can be up to 1600 characters. Split long replies into chunks.
    """
    if message is None:
        print("No message to send")
        return

    if not twilio_client:
        print("Twilio credentials not configured")
        return

    if not TWILIO_WHATSAPP_FROM:
        print("TWILIO_WHATSAPP_FROM not configured")
        return

    text = str(message)
    max_len = 1500  # Twilio limit is 1600, keep a buffer
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)] or [text]

    # Ensure 'to' is in correct format (whatsapp:+countrycode+number)
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    for idx, part in enumerate(chunks, start=1):
        try:
            message_obj = twilio_client.messages.create(
                body=part,
                from_=TWILIO_WHATSAPP_FROM,
                to=to
            )
            print(f"Twilio WhatsApp response (chunk {idx}/{len(chunks)}): SID={message_obj.sid}, Status={message_obj.status}")
        except Exception as e:
            print(f"Twilio WhatsApp error (chunk {idx}/{len(chunks)}): {str(e)}")
            # If the API returns an error, stop sending remaining chunks
            break


def download_media_from_twilio(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)):
    """
    Download media file from Twilio.
    Twilio media URLs require Basic Auth with Account SID and Auth Token.
    """
    import requests
    response = requests.get(media_url, auth=auth)
    response.raise_for_status()
    return response.content


def create_twiml_response(message_text):
    """
    Create a TwiML response for Twilio webhook (if needed for some use cases).
    """
    resp = MessagingResponse()
    resp.message(message_text)
    return str(resp)

