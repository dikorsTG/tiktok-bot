import os
import requests
import yt_dlp
from flask import Flask, request

TOKEN = os.getenv("TOKEN")

print("BOT STARTING...")

if not TOKEN:
    print("❌ TOKEN is missing")
    exit()

API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

WEBHOOK_URL = "https://tiktok-bot-1-3atx.onrender.com/webhook"
SECRET = "1234"  # ✅ теперь используем

# ---------------- HELPERS ----------------

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


# ---------------- TIKTOK ----------------

def download_tiktok(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api, timeout=10).json()

        data = r.get("data", {})

        if data.get("play"):
            return {"type": "video", "url": data["play"]}

        if data.get("images"):
            return {"type": "images", "urls": data["images"]}

        return None

    except Exception as e:
        print("TIKTOK ERROR:", e)
        return None


# ---------------- YOUTUBE ----------------

def download_youtube(url):
    try:
        ydl_opts = {
            "format": "mp4[height<=720]/best",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            duration = info.get("duration", 0)

            if duration > 600:
                return "PRO_ONLY"

            for f in info["formats"][::-1]:
                if f.get("ext") == "mp4" and f.get("url"):
                    return f["url"]

            return None

    except Exception as e:
        print("YT ERROR:", e)
        return None


# ---------------- VIDEO NOTE ----------------

def convert_video_note(chat_id, file_id):
    r = requests.get(f"{API}/getFile?file_id={file_id}").json()
    file_path = r["result"]["file_path"]

    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

    send_video(chat_id, file_url)


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return "🤖 Bot is running"


@app.route("/webhook", methods=["POST"])
def webhook():

    # ✅ ПРОВЕРКА SECRET (теперь работает)
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET:
        print("❌ WRONG SECRET")
        return "forbidden", 403

    data = request.get_json()
    print("INCOMING:", data)

    if not data or "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]

    # 🎬 кружок → видео
    if "video_note" in msg:
        file_id = msg["video_note"]["file_id"]
        send_message(chat_id, "🎬 Конвертирую кружок...")
        convert_video_note(chat_id, file_id)
        return "ok"

    text = msg.get("text")
    if not text:
        return "ok"

    # ---------------- COMMANDS ----------------

    if text == "/start":
        send_message(chat_id, "👋 Отправь TikTok или YouTube ссылку")

    elif text == "/help":
        send_message(chat_id,
            "🤖 Бот умеет:\n\n"
            "📥 TikTok (видео + фото)\n"
            "📺 YouTube (до 10 минут)\n"
            "🎬 кружки → видео\n"
        )

    # ---------------- TIKTOK ----------------

    elif is_tiktok(text):
        send_message(chat_id, "⏳ TikTok загрузка...")

        result = download_tiktok(text)

        if not result:
            send_message(chat_id, "❌ Ошибка TikTok")

        elif result["type"] == "video":
            send_video(chat_id, result["url"])

        elif result["type"] == "images":
            send_message(chat_id, "🖼 Отправляю фото...")
            send_photos(chat_id, result["urls"])

    # ---------------- YOUTUBE ----------------

    elif is_youtube(text):
        send_message(chat_id, "⏳ YouTube загрузка...")

        video = download_youtube(text)

        if video == "PRO_ONLY":
            send_message(chat_id, "🚫 Видео длиннее 10 минут — только PRO")
        elif video:
            send_video(chat_id, video)
        else:
            send_message(chat_id, "❌ Ошибка YouTube")

    return "ok"


# ---------------- WEBHOOK ----------------

def set_webhook():
    print("SETTING WEBHOOK...")
    requests.get(f"{API}/deleteWebhook?drop_pending_updates=true")
    requests.get(
        f"{API}/setWebhook?url={WEBHOOK_URL}&secret_token={SECRET}"
    )
    print("WEBHOOK SET")


# ---------------- START ----------------

if __name__ == "__main__":
    import time

    time.sleep(2)
    set_webhook()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
