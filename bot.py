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
SECRET = "my_super_secret_123"


# --- helpers ---
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


# --- URL checks ---
def is_tiktok(url):
    return "tiktok.com" in url


def is_youtube(url):
    return "youtube.com" in url or "youtu.be" in url


# --- TikTok ---
def download_tiktok(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api, timeout=10).json()
        return r.get("data", {}).get("play")
    except:
        return None


# --- YouTube ---
def download_youtube(url):
    try:
        ydl_opts = {
            "format": "best",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            duration = info.get("duration", 0)  # в секундах

            # ⛔ лимит 10 минут (600 сек)
            if duration > 600:
                return "PRO_ONLY"

            return info.get("url")

    except Exception as e:
        print("YT ERROR:", e)
        return None


# --- convert video note → video ---
def convert_video_note(chat_id, file_id):
    r = requests.get(f"{API}/getFile?file_id={file_id}").json()
    file_path = r["result"]["file_path"]

    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

    send_video(chat_id, file_url)


# --- routes ---
@app.route("/")
def home():
    return "🤖 Bot is running"


@app.route("/webhook", methods=["POST"])
def webhook():

    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET:
        return "forbidden", 403

    data = request.get_json()

    if not data or "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]

    # 🎬 кружок
    if "video_note" in msg:
        file_id = msg["video_note"]["file_id"]
        send_message(chat_id, "🎬 Конвертирую кружок в видео...")
        convert_video_note(chat_id, file_id)
        return "ok"

    text = msg.get("text")

    if not text:
        return "ok"

    # --- commands ---
    if text == "/start":
        send_message(chat_id, "👋 Отправь TikTok или YouTube ссылку")

    elif text == "/help":
        send_message(chat_id,
            "🤖 Бот умеет:\n\n"
            "📥 TikTok скачивание\n"
            "📺 YouTube скачивание\n"
            "🎬 кружки → видео\n\n"
            "⚡ лимит: 10 минут (PRO)"
        )

    # --- TikTok ---
    elif is_tiktok(text):
        send_message(chat_id, "⏳ TikTok загрузка...")

        video = download_tiktok(text)

        if video:
            send_video(chat_id, video)
        else:
            send_message(chat_id, "❌ Ошибка TikTok")

    # --- YouTube ---
    elif is_youtube(text):
        send_message(chat_id, "⏳ YouTube загрузка...")

        video = download_youtube(text)

        if video == "PRO_ONLY":
            send_message(chat_id, "🚫 Видео длиннее 10 минут — доступ только PRO")
        elif video:
            send_video(chat_id, video)
        else:
            send_message(chat_id, "❌ Ошибка YouTube")

    return "ok"


# --- webhook setup ---
def set_webhook():
    print("SETTING WEBHOOK...")
    requests.get(f"{API}/deleteWebhook?drop_pending_updates=true")
    requests.get(f"{API}/setWebhook?url={WEBHOOK_URL}&secret_token={SECRET}")
    print("WEBHOOK SET")


if __name__ == "__main__":
    import time

    time.sleep(2)
    set_webhook()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
