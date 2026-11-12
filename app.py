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

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise ValueError("Missing CHANNEL_ACCESS_TOKEN or CHANNEL_SECRET")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip().lower()

    if text in ["hi", "hello", "hey"]:
        reply = "Hello!\nWelcome to Pandan Milk\n\nType 'menu' to see the sample menu."
    elif text == "menu":
        reply = (
            "Sample Menu\n\n"
            "1. Pandan Milk - 55 THB\n"
            "2. Iced Pandan Milk - 65 THB\n"
            "3. Kanom Krok - 45 THB\n\n"
            "Type 1, 2, or 3 to select"
        )
    elif text in ["1", "2", "3"]:
        items = {
            "1": "Pandan Milk - 55 THB",
            "2": "Iced Pandan Milk - 65 THB",
            "3": "Kanom Krok - 45 THB",
        }
        reply = f"You selected:\n{items[text]}\n\nThank you!\n\nType 'menu' to see the menu again."
    elif text == "help":
        reply = "Type 'menu' to see the sample menu."
    else:
        reply = "Type 'menu' to see the sample menu."

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
