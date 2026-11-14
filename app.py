import os
import requests
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

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
XAI_API_KEY = os.getenv("XAI_API_KEY")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

SYSTEM_PROMPT = """You are the official LINE chatbot for Pandan Milk – From California with Love.
Reply in the same language the customer uses.
Location: SiamScape, 2nd Fl
https://share.google/UCzhNDv8gW53oi6eY
Opening hours: 10:00–22:00 every day.
Promotions: 10% Off Now / 15% Off for Chula Students & Staff.
Be friendly and short. Do not invent prices or take orders."""

@app.route("/")
def home():
    return "OK", 200

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
        return "AI key missing."
    try:
        r = requests.post(
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
                "max_tokens": 250,
            },
            timeout=12,
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return "Sorry, please try again."

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    reply = get_ai_reply(event.message.text.strip())
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
