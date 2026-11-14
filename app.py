import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import requests

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
XAI_API_KEY = os.getenv("XAI_API_KEY")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise ValueError("Missing CHANNEL_ACCESS_TOKEN or CHANNEL_SECRET")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

SYSTEM_PROMPT = """You are the official LINE chatbot for Pandan Milk – From California with Love.

Your Role:
Help customers with menu, location, promotions, and basic questions.
Always reply in the same language the customer uses.

Business Information:
- Brand: Pandan Milk – From California with Love
- Location: SIAMSCAPE
  https://share.google/UCzhNDv8gW53oi6eY
- Opening hours: Every day 10:00–22:00
- Products: Pandan Milk (Classic, Coconut, Special) and Kanom Krok (Original, Pandan)

Current Promotions:
- 10% Off Now
- 15% Off for Chula Students & Staff

When answering about Location, Promotions, or Language, include both Thai and English.
Tone: Friendly, short, mobile-friendly.
Do not invent prices or promotions. Do not take orders."""

@app.route("/")
def home():
    return "LINE Bot is running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK", 200

def get_ai_reply(user_message):
    if not XAI_API_KEY:
        return "AI is not configured yet."
    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-4-fast",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.7,
                "max_tokens": 300,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return "Sorry, I couldn't process that right now."

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()
    reply = get_ai_reply(user_text)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
