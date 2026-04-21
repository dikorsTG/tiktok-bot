import os
import requests
import tempfile
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

WEBHOOK_URL = "https://tiktok-bot-1-3atx.onrender.com/webhook"


# ---------------- SEND ----------------

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


def send_photos(chat_id, images):
    media = [{"type": "photo", "media": img} for img in images[:10]]
    requests.post(API + "/sendMediaGroup", json={
        "chat_id": chat_id,
        "media": media
    })


# ---------------- CHECKS ----------------

def is_tiktok(url):
    return "tiktok.com" in url


def is_youtube(url):
    return "youtube.com" in url or "youtu.be" in url


# ---------------- TIKTOK (СТАБИЛЬНЫЙ) ----------------

def download_tiktok(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api, timeout=10).json()
        data = r.get("data", {})

        if data.get("play"):
            return ("video", data["play"])

        if data.get("images"):
            return ("images", data["images"])

        return None
    except:
        return None


# ---------------- YOUTUBE (БЕЗ СКАЧИВАНИЯ — СТАБИЛЬНО) ----------------

def get_youtube_link(url):
    return url  # просто отдаём ссылку (самый стабильный вариант)


# ---------------- WEBHOOK ----------------

@app.route("/")
def home():
    return "🤖 Bot is running"


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()
    if not data or "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    # ---------------- KRUZHKI ----------------

    if "video_note" in msg:
        send_message(chat_id, "🎬 Кружок получен (пересылаю)")
        file_id = msg["video_note"]["file_id"]

        file = requests.get(f"{API}/getFile?file_id={file_id}").json()
        path = file["result"]["file_path"]
        url = f"https://api.telegram.org/file/bot{TOKEN}/{path}"

        send_video(chat_id, url)
        return "ok"

    # ---------------- COMMANDS ----------------

    if text == "/start":
        send_message(chat_id, "👋 Отправь TikTok или YouTube ссылку")

    elif text == "/help":
        send_message(chat_id,
            "🤖 Бот:\n\n"
            "📥 TikTok\n"
            "📺 YouTube (отправка ссылки)\n"
            "🎬 кружки"
        )

    # ---------------- TIKTOK ----------------

    elif is_tiktok(text):
        send_message(chat_id, "⏳ TikTok...")

        result = download_tiktok(text)

        if not result:
            send_message(chat_id, "❌ Ошибка TikTok")

        elif result[0] == "video":
            send_video(chat_id, result[1])

        elif result[0] == "images":
            send_photos(chat_id, result[1])

    # ---------------- YOUTUBE ----------------

    elif is_youtube(text):
        send_message(chat_id, "📺 YouTube ссылка:")
        send_message(chat_id, get_youtube_link(text))

    return "ok"


# ---------------- START ----------------

if __name__ == "__main__":
    import time
    time.sleep(2)

    requests.get(f"{API}/deleteWebhook")
    requests.get(f"{API}/setWebhook?url={WEBHOOK_URL}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
