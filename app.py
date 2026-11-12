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

    if text in ["hi", "hello", "hey", "สวัสดี", "start"]:
        reply = (
            "สวัสดีครับ / Hello!\n"
            "Welcome to Pandan Milk\n"
            "From California with Love\n\n"
            "พิมพ์ 'menu' หรือ 'เมนู' เพื่อดูเมนู\n"
            "Type 'menu' to see the menu"
        )
    elif text in ["menu", "เมนู", "เมนูอาหาร"]:
        reply = (
            "Pandan Milk Menu\n"
            "เมนู Pandan Milk\n\n"
            "1. Pandan Milk (Classic) - 55 THB\n"
            "   นมใบเตย คลาสสิก\n\n"
            "2. Pandan Milk (Less Sugar) - 55 THB\n"
            "   นมใบเตย หวานน้อย\n\n"
            "3. Iced Pandan Milk - 65 THB\n"
            "   นมใบเตย เย็น\n\n"
            "4. Kanom Krok (6 pcs) - 45 THB\n"
            "   ขนมครกใบเตย 6 ชิ้น\n\n"
            "Type the number (1-4) to order\n"
            "พิมพ์ตัวเลข (1-4) เพื่อสั่ง"
        )
    elif text in ["1", "2", "3", "4"]:
        items = {
            "1": "Pandan Milk (Classic) - 55 THB",
            "2": "Pandan Milk (Less Sugar) - 55 THB",
            "3": "Iced Pandan Milk - 65 THB",
            "4": "Kanom Krok (6 pcs) - 45 THB",
        }
        reply = (
            f"You selected:\n{items[text]}\n\n"
            "Please confirm your order at the kiosk.\n"
            "กรุณายืนยันออเดอร์ที่ร้าน\n\n"
            "Type 'menu' to see the menu again."
        )
    elif text in ["help", "ช่วย", "ช่วยเหลือ"]:
        reply = (
            "Commands / คำสั่ง:\n"
            "- menu / เมนู\n"
            "- 1, 2, 3, 4 to order\n"
            "- help"
        )
    else:
        reply = (
            "Sorry, I didn't understand.\n"
            "ขออภัย ไม่เข้าใจ\n\n"
            "Type 'menu' or 'เมนู' to see the menu."
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
