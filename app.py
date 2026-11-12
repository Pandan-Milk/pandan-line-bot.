import os
from datetime import datetime
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

# Discount codes and their expiry dates
DISCOUNT_CODES = {
    "CHULA15-2027": {
        "discount": 15,
        "expiry": "2027-12-31",
        "description": "15% Chula Community Discount"
    }
}

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

def check_discount_code(code):
    code = code.strip().upper()
    if code not in DISCOUNT_CODES:
        return None, "Invalid code."
    
    info = DISCOUNT_CODES[code]
    expiry_date = datetime.strptime(info["expiry"], "%Y-%m-%d").date()
    today = datetime.now().date()
    
    if today > expiry_date:
        return None, f"This code expired on {info['expiry']}."
    
    return info, None

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    text_lower = text.lower()

    if text_lower in ["hi", "hello", "hey"]:
        reply = "Hello!\nWelcome to Pandan Milk\n\nType 'menu' to see the sample menu.\nType a discount code (e.g. CHULA15-2027) to apply discount."
    elif text_lower == "menu":
        reply = (
            "Sample Menu\n\n"
            "1. Pandan Milk - 55 THB\n"
            "2. Iced Pandan Milk - 65 THB\n"
            "3. Kanom Krok - 45 THB\n\n"
            "Type 1, 2, or 3 to select\n"
            "Or type a discount code to apply 15% off"
        )
    elif text_lower in ["1", "2", "3"]:
        items = {
            "1": ("Pandan Milk", 55),
            "2": ("Iced Pandan Milk", 65),
            "3": ("Kanom Krok", 45),
        }
        name, price = items[text_lower]
        reply = f"You selected:\n{name} - {price} THB\n\nType a discount code to apply discount, or type 'menu' again."
    else:
        # Check if it's a discount code
        info, error = check_discount_code(text)
        if error:
            reply = f"{error}\n\nType 'menu' to see the sample menu."
        else:
            reply = (
                f"✅ Valid!\n"
                f"{info['description']}\n"
                f"Discount: {info['discount']}%\n"
                f"Expires: {info['expiry']}\n\n"
                f"Please show this message at the kiosk.\n"
                f"Type 'menu' to continue."
            )

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
