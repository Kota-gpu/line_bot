from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

app = Flask(__name__)

# 環境變數（Render 上設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
YOUR_USER_ID = os.getenv("LINE_USER_ID")  # 你要發訊息的對象

assert LINE_CHANNEL_ACCESS_TOKEN, "LINE_CHANNEL_ACCESS_TOKEN not set"
assert LINE_CHANNEL_SECRET, "LINE_CHANNEL_SECRET not set"
assert YOUR_USER_ID, "LINE_USER_ID not set"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- 定時任務 ---
def send_daily_message():
    try:
        message = TextSendMessage(text="Fluffy is the best cat in the world")
        line_bot_api.push_message(YOUR_USER_ID, message)
        print(f"[{datetime.now()}] Sent daily message.")
    except Exception as e:
        print(f"[Error sending scheduled message] {e}")

# 啟動排程器
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(send_daily_message, 'cron', hour=0, minute=10)
scheduler.start()

# --- Flask 路由 ---
@app.route("/")
def home():
    return "LINE Bot with Scheduler is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error in webhook handler: {e}")
        return "Bad Request", 400
    return "OK"

# --- 處理 LINE 訊息事件 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    if text.lower() == "提醒我":
        reply = "你設定的提醒將在每天晚上 11:35 傳送給你！"
    else:
        reply = f"你剛說的是：{text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# --- 執行 Flask App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
