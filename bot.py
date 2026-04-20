import os
import requests
from flask import Flask, request

TOKEN = os.getenv("TOKEN")

print("BOT STARTING...")

if not TOKEN:
    print("❌ TOKEN is missing")
    exit()

API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)  # ✅ исправлено

WEBHOOK_URL = "https://tiktok-bot-1-3atx.onrender.com/webhook"
SECRET = "my_super_secret_123"


# --- Telegram helpers ---
def send_message(chat_id, text):
    requests.post(API + "/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


def send_video(chat_id, url):
    requests.post(API + "/sendVideo", json={
        "chat_id": chat_id,
        "video": url
    })


def send_video_note(chat_id, file_id):
    # получаем файл от Telegram
    r = requests.get(f"{API}/getFile?file_id={file_id}").json()
    file_path = r["result"]["file_path"]

    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

    # отправляем как кружок
    requests.post(API + "/sendVideoNote", json={
        "chat_id": chat_id,
        "video_note": file_url
    })


# --- TikTok ---
def is_tiktok(url):
    return "tiktok.com" in url


def download_video(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api, timeout=10).json()
        return r.get("data", {}).get("play")
    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        return None


# --- routes ---
@app.route("/")
def home():
    return "🤖 TikTok bot is running"


@app.route("/webhook", methods=["POST"])
def webhook():
    # 🔐 защита
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET:
        return "forbidden", 403

    data = request.get_json()

    if not data or "message" not in data:
        return "ok"

    message = data["message"]
    chat_id = message["chat"]["id"]

    # --- 🎥 если пришёл кружок ---
    if "video_note" in message:
        file_id = message["video_note"]["file_id"]

        send_message(chat_id, "🔄 Пересылаю кружок...")
        send_video_note(chat_id, file_id)

        return "ok"

    text = message.get("text")

    if not text:
        return "ok"

    print("CHAT:", chat_id, "TEXT:", text)

    if text == "/start":
        send_message(chat_id, "👋 Бот работает! Отправь TikTok ссылку 📥")

    elif text == "/help":
        send_message(chat_id,
            "🤖 Что умеет бот:\n\n"
            "📥 TikTok — скачивает видео\n"
            "🎥 Кружки — пересылает кружок\n\n"
            "📌 Просто отправь ссылку или кружок"
        )

    elif is_tiktok(text):
        send_message(chat_id, "⏳ Скачиваю TikTok...")

        video = download_video(text)

        if video:
            send_video(chat_id, video)
        else:
            send_message(chat_id, "❌ Не удалось скачать видео")

    return "ok"


# --- webhook setup ---
def set_webhook():
    try:
        print("SETTING WEBHOOK...")
        requests.get(f"{API}/deleteWebhook?drop_pending_updates=true")
        requests.get(
            f"{API}/setWebhook?url={WEBHOOK_URL}&secret_token={SECRET}"
        )
        print("WEBHOOK SET")
    except Exception as e:
        print("WEBHOOK ERROR:", e)


# --- запуск ---
if __name__ == "__main__":  # ✅ исправлено
    import time

    time.sleep(2)

    set_webhook()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
