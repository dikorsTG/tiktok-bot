import os
import requests
from flask import Flask, request

TOKEN = os.getenv("TOKEN")

print("BOT STARTING...")

if not TOKEN:
    print("❌ TOKEN is missing")
    exit()

API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(name)

WEBHOOK_URL = "https://tiktok-bot-1-3atx.onrender.com/webhook"
SECRET = "my_super_secret_123"  # 🔐 придумай любой


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
    # 🔐 проверка что это Telegram
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != SECRET:
        print("❌ NOT TELEGRAM")
        return "forbidden", 403

    data = request.get_json()

    if not data or "message" not in data:
        return "ok"

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text")

    if not text:
        return "ok"

    print("CHAT:", chat_id, "TEXT:", text)

    if text == "/start":
        send_message(chat_id, "👋 Бот работает! Отправь TikTok ссылку 📥")

    elif text == "/help":
        send_message(chat_id, "📌 Просто отправь TikTok ссылку")

    elif is_tiktok(text):
        send_message(chat_id, "⏳ Скачиваю...")

        video = download_video(text)

        if video:
            send_video(chat_id, video)
        else:
            send_message(chat_id, "❌ Не удалось скачать видео")

    else:
        return "ok"   # ❗ убрали спам

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


if name == "main":
    import time

    time.sleep(2)

    set_webhook()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
