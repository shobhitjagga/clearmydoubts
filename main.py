from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from gemini_utils import extract_question_from_image, generate_answer
from supabase_utils import fetch_rag_context,create_embedding
import json

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    response = requests.post(url, json=data, headers=headers)
    print("WhatsApp response:", response.json())

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    # DEBUG: print the incoming WhatsApp message
    print("Received WhatsApp payload:", json.dumps(data, indent=2))

    try:
        entry = data["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]
        sender = message["from"]

        # If image
        if "image" in message:
            media_id = message["image"]["id"]

            # get media URL
            media_url = f"https://graph.facebook.com/v20.0/{media_id}"
            media_resp = requests.get(
                media_url,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            ).json()

            file_url = media_resp["url"]
            img_bytes = requests.get(
                file_url,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            ).content

            # extract question
            question = extract_question_from_image(img_bytes)

            # RAG context
            q_embed = create_embedding(question)
            context = fetch_rag_context(q_embed)

            # generate answer
            answer = generate_answer(question, context)

            send_whatsapp_message(sender, answer)
            return {"status": "processed"}

        # If text message
        if "text" in message:
            question = message["text"]["body"]
            q_embed = create_embedding(question)
            context = fetch_rag_context(q_embed)
            answer = generate_answer(question, context)
            send_whatsapp_message(sender, answer)
            return {"status": "processed"}

    except Exception as e:
        print("Error:", e)
        return {"status": "error"}

    return {"status": "ignored"}

# For webhook verification
@app.get("/webhook")
async def verify_token(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == "mytoken":
        return int(params.get("hub.challenge"))
    return "Invalid"

@app.get("/")
def root():
    return {"status": "Clearmydoubts API is live"}
