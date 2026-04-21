import os
import requests
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


def send_audio(chat_id, url):
    requests.post(API + "/sendAudio", json={
        "chat_id": chat_id,
        "audio": url
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


# ---------------- TIKTOK ----------------

def download_tiktok(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api, timeout=10).json()
        data = r.get("data", {})

        return {
            "video": data.get("play"),
            "images": data.get("images"),
            "music": data.get("music"),
            "title": data.get("title")
        }

    except:
        return None


# ---------------- YOUTUBE ----------------

def get_youtube_link(url):
    return url  # стабильный вариант


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
        send_message(chat_id, "🎬 Кружок получен")

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
            "🤖 Бот умеет:\n\n"
            "📥 TikTok (видео / фото / звук)\n"
            "📺 YouTube (ссылка)\n"
            "🎬 кружки → видео"
        )

    # ---------------- TIKTOK ----------------

    elif is_tiktok(text):
        send_message(chat_id, "⏳ TikTok...")

        result = download_tiktok(text)

        if not result:
            send_message(chat_id, "❌ Ошибка TikTok")
            return "ok"

        # 1. VIDEO
        if result.get("video"):
            send_message(chat_id, "🎬 Видео")
            send_video(chat_id, result["video"])

        # 2. MUSIC
        if result.get("music"):
            send_message(chat_id, "🎵 Звук")
            send_audio(chat_id, result["music"])

        # 3. IMAGES
        if result.get("images"):
            send_message(chat_id, "🖼 Фото")
            send_photos(chat_id, result["images"])

        # 4. DESCRIPTION
        if result.get("title"):
            send_message(chat_id, f"📌 {result['title']}")

    # ---------------- YOUTUBE ----------------

    elif is_youtube(text):
        send_message(chat_id, "📺 YouTube:")
        send_message(chat_id, get_youtube_link(text))

    return "ok"


# ---------------- START ----------------

if __name__ == "__main__":
    import time
    time.sleep(2)

    requests.get(f"{API}/deleteWebhook")
    requests.get(f"{API}/setWebhook?url={WEBHOOK_URL}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
