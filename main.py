from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from gemini_utils import extract_question_from_image, generate_answer, create_embedding
from supabase_utils import fetch_rag_context
import json

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

def send_whatsapp_message(to, message):
    """
    WhatsApp text body must be <= 4096 chars. Split long replies into chunks.
    """
    if message is None:
        print("No message to send")
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

        print(f"WhatsApp response (chunk {idx}/{len(chunks)}):", resp_json)

        # If the API returns an error, stop sending remaining chunks to avoid spam
        if response.status_code >= 400:
            break

@app.post("/webhook")
@app.post("/whatsapp_webhook")
async def whatsapp_webhook(request: Request):
    try:
        data = await request.json()
        
        # DEBUG: print the incoming WhatsApp message
        print("=" * 50)
        print("Received WhatsApp payload:")
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

            # get media URL
            media_url = f"https://graph.facebook.com/v20.0/{media_id}"
            media_resp = requests.get(
                media_url,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            )
            media_resp.raise_for_status()
            media_data = media_resp.json()

            file_url = media_data["url"]
            img_resp = requests.get(
                file_url,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            )
            img_resp.raise_for_status()
            img_bytes = img_resp.content

            # extract question
            print("Extracting question from image...")
            question = extract_question_from_image(img_bytes)
            print(f"Extracted question: {question}")

            # RAG context
            print("Fetching RAG context...")
            q_embed = create_embedding(question)
            context = fetch_rag_context(q_embed)

            # generate answer
            print("Generating answer...")
            answer = generate_answer(question, context)
            print(f"Generated answer: {answer[:100]}...")

            send_whatsapp_message(sender, answer)
            return {"status": "processed", "type": "image"}

        # If text message
        if "text" in message:
            print("Processing text message")
            question = message["text"]["body"]
            print(f"Question: {question}")

            # RAG context
            print("Fetching RAG context...")
            q_embed = create_embedding(question)
            context = fetch_rag_context(q_embed)

            # generate answer
            print("Generating answer...")
            answer = generate_answer(question, context)
            print(f"Generated answer: {answer[:100]}...")

            send_whatsapp_message(sender, answer)
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

# For webhook verification
@app.get("/webhook")
async def verify_token(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == "mytoken":
        return int(params.get("hub.challenge"))
    return "Invalid"

@app.get("/")
def root():
    return {"status": "Clearmydoubts API is live", "endpoints": ["/webhook", "/whatsapp_webhook", "/health"]}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "clearmydoubts",
        "endpoints": {
            "webhook": "/webhook",
            "whatsapp_webhook": "/whatsapp_webhook",
            "health": "/health"
        }
    }
