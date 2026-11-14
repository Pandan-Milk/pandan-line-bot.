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
    if datetime.now().date() > expiry_date:
        return None, f"This code expired on {info['expiry']}."
    return info, None

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    text_lower = text.lower()

    # Rich Menu buttons
    if "เมนู" in text or text_lower == "menu":
        reply = (
            "Pandan Milk Menu\n\n"
            "1. Pandan Milk - 55 THB\n"
            "2. Iced Pandan Milk - 65 THB\n"
            "3. Kanom Krok - 45 THB\n\n"
            "Type 1, 2, or 3 to select"
        )
    elif "สาขา" in text or "location" in text_lower:
        reply = "Location:\nSiam Escape / your kiosk address here\n\nType 'menu' to see the menu."
    elif "โปรโมชัน" in text or "promo" in text_lower:
        reply = (
            "Current Promo:\n"
            "15% off for Chula students & staff\n"
            "Use code: CHULA15-2027\n\n"
            "Type the code to apply."
        )
    elif "แชท" in text or "chat" in text_lower:
        reply = "You are already chatting with us!\nHow can we help you today?\nType 'menu' to see the menu."
    elif "เกี่ยวกับเรา" in text or "about" in text_lower:
        reply = "Pandan Milk\nFrom California with Love\n\nFresh pandan milk & kanom krok."
    elif "ภาษา" in text or "language" in text_lower:
        reply = "Language: English / ไทย\n\nType 'menu' or 'เมนู' anytime."
    
    # Discount code
    elif text.upper() in DISCOUNT_CODES or text.upper().startswith("CHULA"):
        info, error = check_discount_code(text)
        if error:
            reply = error
        else:
            reply = (
                f"✅ Valid!\n{info['description']}\n"
                f"Discount: {info['discount']}%\n"
                f"Expires: {info['expiry']}\n\n"
                "Please show this message at the kiosk."
            )
    
    # Menu item selection
    elif text_lower in ["1", "2", "3"]:
        items = {
            "1": "Pandan Milk - 55 THB",
            "2": "Iced Pandan Milk - 65 THB",
            "3": "Kanom Krok - 45 THB",
        }
        reply = f"You selected:\n{items[text_lower]}\n\nType a discount code if you have one."
    
    # Default
    else:
        reply = "Type 'menu' to see the menu\nor tap the Menu button below."

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
