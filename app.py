from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pytz import timezone
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

# 發送客製訊息
def send_custom_message(text):
    message = TextSendMessage(text=text)
    for user_id in subscribed_users:
        try:
            line_bot_api.push_message(user_id, message)
            print(f"[{datetime.now()}] Sent: '{text}' to {user_id}")
        except Exception as e:
            print(f"[Error sending to {user_id}]: {e}")

# 啟動排程器：多個時間提醒
tz = timezone('Asia/Taipei')
scheduler = BackgroundScheduler(daemon=True)

scheduler.add_job(lambda: send_custom_message("早安🌅，該享用營養豐盛的早餐囉！別忘了飯後服用早上的藥品，祝您一天元氣滿滿💪"),
                  'cron', hour=8, minute=0, timezone=tz)

scheduler.add_job(lambda: send_custom_message("中午好🍱，該吃飯囉！飯後請服用午餐藥品，保護健康，讓午後也精神飽滿✨"),
                  'cron', hour=12, minute=0, timezone=tz)

scheduler.add_job(lambda: send_custom_message("下午好，💧 喝一杯清水，補充水分，🧘‍♂️ 伸展一下手腳，動動筋骨，健康從小動作開始，祝您購物愉快、神清氣爽！😊 運動挑戰連結: https://kota-gpu.github.io/line_bot/"),
                  'cron', hour=14, minute=0, timezone=tz)

scheduler.add_job(lambda: send_custom_message("傍晚好🌇，準備享用美味晚餐！餐後請記得服用晚餐藥品，祝您今晚好好休息😉"),
                  'cron', hour=18, minute=0, timezone=tz)

scheduler.add_job(lambda: send_custom_message("夜深了🌙，該準備就寢了。在睡前請服用臨睡前藥品，安穩入眠，明早再見👋"),
                  'cron', hour=22, minute=0, timezone=tz)

scheduler.start()

@app.route("/")
def home():
    return "LINE Bot with multiple daily reminders is running!"

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
            reply = "你已成功訂閱每日提醒！每天四次貼心服藥提醒以及運動挑戰將送達 💪"
        else:
            reply = "你已經訂閱過囉～請靜候每日的小提醒 😉"
    else:
        reply = f"你剛說的是：{event.message.text}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
