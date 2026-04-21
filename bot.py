import os
import requests
import yt_dlp
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


def send_video(chat_id, file):
    if isinstance(file, str) and file.startswith("http"):
        requests.post(API + "/sendVideo", json={
            "chat_id": chat_id,
            "video": file
        })
    else:
        with open(file, "rb") as f:
            requests.post(API + "/sendVideo",
                data={"chat_id": chat_id},
                files={"video": f}
            )


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
            return ("video", data["play"])

        if data.get("images"):
            return ("images", data["images"])

        return None
    except:
        return None


# ---------------- YOUTUBE (ФАЙЛ) ----------------

def download_youtube(url):
    try:
        temp_dir = tempfile.mkdtemp()
        output = os.path.join(temp_dir, "video.mp4")

        ydl_opts = {
            "format": "mp4[height<=720]/best",
            "outtmpl": output,
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if info.get("duration", 0) > 600:
                return "PRO"

        return output

    except Exception as e:
        print("YT ERROR:", e)
        return None


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

    # ---------------- COMMANDS ----------------

    if text == "/start":
        send_message(chat_id, "👋 Отправь TikTok или YouTube ссылку")

    elif text == "/help":
        send_message(chat_id,
            "🤖 Бот:\n\n"
            "📥 TikTok (видео + фото)\n"
            "📺 YouTube (до 10 мин)\n"
            "🎬 кружки → видео"
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
            send_message(chat_id, "🖼 фото...")
            send_photos(chat_id, result[1])

    # ---------------- YOUTUBE ----------------

    elif is_youtube(text):
        send_message(chat_id, "⏳ YouTube скачивание...")

        file_path = download_youtube(text)

        if file_path == "PRO":
            send_message(chat_id, "🚫 Видео >10 минут (PRO)")
        elif file_path:
            send_video(chat_id, file_path)
        else:
            send_message(chat_id, "❌ Ошибка YouTube")

    return "ok"


# ---------------- START ----------------

if __name__ == "__main__":
    import time
    time.sleep(2)

    requests.get(f"{API}/deleteWebhook")
    requests.get(f"{API}/setWebhook?url={WEBHOOK_URL}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
