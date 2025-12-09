from fastapi import FastAPI, Request
from fastapi.responses import Response
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from supabase_utils import fetch_rag_context
from latex_converter import convert_math_expressions
from markdown_formatter import format_answer_for_whatsapp
import json

# Import both AI providers
from gemini_utils import (
    extract_question_from_image as extract_question_gemini,
    generate_answer as generate_answer_gemini,
    create_embedding as create_embedding_gemini
)
from openai_utils import (
    extract_question_from_image as extract_question_openai,
    generate_answer as generate_answer_openai,
    create_embedding as create_embedding_openai
)

# Import both WhatsApp providers
from whatsapp_cloud_api import send_whatsapp_message as send_whatsapp_cloud, get_media_url, download_media as download_media_cloud
from twilio_whatsapp import send_whatsapp_message as send_whatsapp_twilio, download_media_from_twilio

app = FastAPI()

# AI Provider selection: "gpt" or "gemini" (defaults to "gpt")
AI_PROVIDER = os.getenv("AI_PROVIDER", "gpt").lower()

# WhatsApp Provider selection: "twilio" or "whatsapp_cloud" (defaults to whatsapp_cloud for backward compatibility)
WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "whatsapp_cloud").lower()

# Legacy WhatsApp Cloud API credentials (still used if provider is whatsapp_cloud)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


def send_message(to, message, provider=None):
    """
    Unified function to send WhatsApp messages via the configured provider.
    Falls back to provider selection if not specified.
    Formats markdown and converts LaTeX to plain text before sending.
    WhatsApp/Twilio don't support Markdown or LaTeX rendering.
    """
    provider = provider or WHATSAPP_PROVIDER
    
    # Format markdown and convert LaTeX to plain text before sending
    # WhatsApp and Twilio don't support Markdown or LaTeX rendering
    if message:
        message = format_answer_for_whatsapp(str(message))
    
    if provider == "twilio":
        send_whatsapp_twilio(to, message)
    else:  # whatsapp_cloud (default)
        send_whatsapp_cloud(to, message)


def get_ai_functions(ai_provider=None):
    """
    Get the appropriate AI functions based on the selected provider.
    """
    ai_provider = ai_provider or AI_PROVIDER
    
    if ai_provider == "gemini":
        return {
            "extract_question": extract_question_gemini,
            "generate_answer": generate_answer_gemini,
            "create_embedding": create_embedding_gemini
        }
    else:  # gpt (default)
        return {
            "extract_question": extract_question_openai,
            "generate_answer": generate_answer_openai,
            "create_embedding": create_embedding_openai
        }


def process_question_and_respond(sender, question, whatsapp_provider=None, ai_provider=None):
    """
    Process a question using RAG and send the answer via the configured providers.
    """
    whatsapp_provider = whatsapp_provider or WHATSAPP_PROVIDER
    ai_provider = ai_provider or AI_PROVIDER
    
    print(f"Processing question using AI provider: {ai_provider}, WhatsApp provider: {whatsapp_provider}")
    print(f"Question: {question}")
    
    # Get AI functions based on provider
    ai_funcs = get_ai_functions(ai_provider)
    
    # # RAG context
    print("Fetching RAG context...")
    q_embed = ai_funcs["create_embedding"](question)
    context = fetch_rag_context(q_embed)
    
    # generate answer
    print("Generating answer...")
    answer = ai_funcs["generate_answer"](question, context)
    print(f"Generated answer: {answer[:100]}...")
    # answer = "This is a test answer"
    send_message(sender, answer, whatsapp_provider)

@app.post("/webhook")
@app.post("/whatsapp_webhook")
async def whatsapp_cloud_webhook(request: Request):
    """
    WhatsApp Cloud API webhook endpoint (original implementation).
    Handles Meta/Facebook WhatsApp Business API webhooks.
    """
    try:
        data = await request.json()
        
        # DEBUG: print the incoming WhatsApp message
        print("=" * 50)
        print("Received WhatsApp Cloud API payload:")
        print(json.dumps(data, indent=2))
        print("=" * 50)

        # Handle webhook verification (GET request is handled separately)
        if "hub" in data and "challenge" in data.get("hub", {}):
            return {"status": "verification"}

        entry = data.get("entry", [])
        if not entry:
            print("No entry found in payload")
            return {"status": "ignored", "reason": "no_entry"}

        changes = entry[0].get("changes", [])
        if not changes:
            print("No changes found in entry")
            return {"status": "ignored", "reason": "no_changes"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            print("No messages found in value")
            return {"status": "ignored", "reason": "no_messages"}

        message = messages[0]
        sender = message.get("from")
        
        if not sender:
            print("No sender found in message")
            return {"status": "ignored", "reason": "no_sender"}

        print(f"Processing message from sender: {sender}")

        # If image
        if "image" in message:
            print("Processing image message")
            media_id = message["image"]["id"]

            # get media URL and download
            file_url = get_media_url(media_id)
            img_bytes = download_media_cloud(file_url)

            # extract question using selected AI provider
            print(f"Extracting question from image using {AI_PROVIDER}...")
            ai_funcs = get_ai_functions()
            question = ai_funcs["extract_question"](img_bytes)
            print(f"Extracted question: {question}")

            process_question_and_respond(sender, question, whatsapp_provider="whatsapp_cloud")
            return {"status": "processed", "type": "image"}

        # If text message
        if "text" in message:
            print("Processing text message")
            question = message["text"]["body"]
            process_question_and_respond(sender, question, whatsapp_provider="whatsapp_cloud")
            return {"status": "processed", "type": "text"}

        print("Message type not supported")
        return {"status": "ignored", "reason": "unsupported_message_type"}

    except KeyError as e:
        error_msg = f"Missing key in payload: {str(e)}"
        print(f"Error: {error_msg}")
        print(f"Payload keys: {list(data.keys()) if 'data' in locals() else 'N/A'}")
        return {"status": "error", "message": error_msg}
    except requests.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(f"Error: {error_msg}")
        return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"Error: {error_msg}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": error_msg}


@app.post("/twilio_webhook")
async def twilio_webhook(request: Request):
    """
    Twilio WhatsApp webhook endpoint.
    Handles incoming messages from Twilio WhatsApp API.
    """
    try:
        # Twilio sends form data, not JSON
        form_data = await request.form()
        
        # DEBUG: print the incoming Twilio message
        print("=" * 50)
        print("Received Twilio WhatsApp payload:")
        for key, value in form_data.items():
            print(f"{key}: {value}")
        print("=" * 50)

        # Extract message data from Twilio webhook
        sender = form_data.get("From", "").replace("whatsapp:", "")  # Remove whatsapp: prefix
        message_body = form_data.get("Body", "")
        num_media = int(form_data.get("NumMedia", "0"))
        
        if not sender:
            print("No sender found in Twilio payload")
            return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                          media_type="application/xml")

        print(f"Processing Twilio message from sender: {sender}")

        # Handle image messages
        if num_media > 0:
            print("Processing image message from Twilio")
            media_url = form_data.get("MediaUrl0")
            if media_url:
                try:
                    # Download image from Twilio
                    img_bytes = download_media_from_twilio(media_url)
                    
                    # extract question using selected AI provider
                    print(f"Extracting question from image using {AI_PROVIDER}...")
                    ai_funcs = get_ai_functions()
                    question = ai_funcs["extract_question"](img_bytes)
                    print(f"Extracted question: {question}")
                    
                    process_question_and_respond(sender, question, whatsapp_provider="twilio")
                    return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                                  media_type="application/xml")
                except Exception as e:
                    print(f"Error processing Twilio image: {str(e)}")
                    return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                                  media_type="application/xml")

        # Handle text messages
        if message_body:
            print("Processing text message from Twilio")
            process_question_and_respond(sender, message_body, whatsapp_provider="twilio")
            return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                          media_type="application/xml")

        print("No message content found in Twilio payload")
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                      media_type="application/xml")

    except Exception as e:
        error_msg = f"Unexpected error in Twilio webhook: {str(e)}"
        print(f"Error: {error_msg}")
        import traceback
        traceback.print_exc()
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                      media_type="application/xml")

# For webhook verification
@app.get("/webhook")
async def verify_token(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == "mytoken":
        return int(params.get("hub.challenge"))
    return "Invalid"

@app.get("/")
def root():
    return {
        "status": "Clearmydoubts API is live",
        "ai_provider": AI_PROVIDER,
        "whatsapp_provider": WHATSAPP_PROVIDER,
        "endpoints": {
            "whatsapp_cloud": ["/webhook", "/whatsapp_webhook"],
            "twilio": ["/twilio_webhook"],
            "health": "/health"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "clearmydoubts",
        "ai_provider": AI_PROVIDER,
        "whatsapp_provider": WHATSAPP_PROVIDER,
        "endpoints": {
            "whatsapp_cloud_webhook": "/webhook",
            "whatsapp_cloud_webhook_alt": "/whatsapp_webhook",
            "twilio_webhook": "/twilio_webhook",
            "health": "/health"
        },
        "providers_configured": {
            "ai": {
                "gpt": bool(os.getenv("OPENAI_API_KEY")),
                "gemini": bool(os.getenv("GEMINI_API_KEY"))
            },
            "whatsapp": {
                "whatsapp_cloud": bool(WHATSAPP_TOKEN and PHONE_ID),
                "twilio": bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("TWILIO_WHATSAPP_FROM"))
            }
        }
    }
