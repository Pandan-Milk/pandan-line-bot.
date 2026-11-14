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

Your Role:
Help customers with menu, location, promotions, and basic questions.
Always reply in the same language the customer uses.
If they write in Thai → reply in Thai.
If they write in English → reply in English.
If they write in Chinese, Korean, Vietnamese, or Arabic → reply in that language as accurately as possible.

Business Information:
- Brand: Pandan Milk – From California with Love
- Current location: Siam Scape, 2nd floor
- Opening hours: Every day 10:00–22:00
- Products: Pandan Milk (Classic, Coconut, Special) and Kanom Krok (Original, Pandan)
- No online ordering yet
- No loyalty points system yet

Core Tasks:
1. Menu Inquiry → list items clearly and mention full menu is available at the kiosk.
2. Location & Opening Hours → give Siam Scape 2nd floor + 10:00–22:00.
3. Promotions → share the current promotion only (do not invent).
4. General Questions → answer about taste, ingredients, how to find the kiosk, etc.
5. Language Handling → Detect the language of the customer’s message and reply in the same language. No need to ask which language they prefer. Keep replies natural and clear.
6. When You Don’t Know → Politely say you don’t have the information and suggest visiting the kiosk or waiting for staff.
7. Tone → Friendly, short, mobile-friendly. Use light emojis when appropriate.

Things You Must NOT Do:
- Do not invent prices or promotions
- Do not take orders
- Do not give health advice"""

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
        return "AI is not configured."
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
