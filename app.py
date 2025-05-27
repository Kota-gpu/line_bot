from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import json

app = Flask(__name__)

# 環境變數（Render 上設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

assert LINE_CHANNEL_ACCESS_TOKEN, "LINE_CHANNEL_ACCESS_TOKEN not set"
assert LINE_CHANNEL_SECRET, "LINE_CHANNEL_SECRET not set"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

SUBSCRIBERS_FILE = "subscribers.json"

# 載入已訂閱用戶
def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()
    with open(SUBSCRIBERS_FILE, "r") as f:
        return set(json.load(f))

# 儲存訂閱用戶
def save_subscribers(users):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(users), f)

subscribed_users = load_subscribers()

# 定時發送訊息
def send_daily_message():
    message = TextSendMessage(text="Fluffy is the best cat in the world")
    for user_id in subscribed_users:
        try:
            line_bot_api.push_message(user_id, message)
            print(f"[{datetime.now()}] Sent reminder to {user_id}")
        except Exception as e:
            print(f"[Error sending to {user_id}]: {e}")

# 啟動排程器：每天中午 12:10 發送訊息
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(send_daily_message, 'cron', hour=0, minute=18)
scheduler.start()

@app.route("/")
def home():
    return "LINE Bot with daily reminder is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Webhook error: {e}")
        return "Bad Request", 400
    return "OK"

# 處理來自 LINE 的文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if text == "提醒我":
        if user_id not in subscribed_users:
            subscribed_users.add(user_id)
            save_subscribers(subscribed_users)
            reply = "你已成功訂閱每日提醒！🐱 每天中午 12:30 會收到 Fluffy 的小秘密～"
        else:
            reply = "你已經訂閱過囉～請靜候 Fluffy 的每日溫馨提醒 🐾"
    else:
        reply = f"你剛說的是：{event.message.text}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
