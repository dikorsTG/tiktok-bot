import os
import time
import requests
from flask import Flask, request
from telegram import Bot, Update

TOKEN = os.getenv("TOKEN")

print("BOT STARTING...")

# --- ❗ ЖЁСТКАЯ ПРОВЕРКА TOKEN ---
if not TOKEN:
    print("❌ TOKEN is missing")
    exit()

print("TOKEN OK")

bot = Bot(token=TOKEN)

app = Flask(__name__)

# --- 🔥 WEBHOOK ---
WEBHOOK_URL = "https://tiktok-bot-1-3atx.onrender.com/webhook"

@app.before_first_request
def setup_webhook():
    try:
        print("SETTING WEBHOOK...")
        bot.delete_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        print("WEBHOOK SET:", WEBHOOK_URL)
    except Exception as e:
        print("WEBHOOK ERROR:", e)


# --- TikTok логика ---
def is_tiktok(url):
    return "tiktok.com" in url


def download_video(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api, timeout=10).json()

        if r.get("data") and r["data"].get("play"):
            return r["data"]["play"]

        return None
    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        return None


# --- команды ---
def start(chat_id):
    bot.send_message(chat_id, "👋 Бот работает! Отправь TikTok ссылку 📥")


def help_cmd(chat_id):
    bot.send_message(chat_id,
        "📌 Как пользоваться:\n\n"
        "1. Отправь TikTok ссылку\n"
        "2. Получишь видео\n\n"
        "/start - запуск\n"
        "/help - помощь"
    )


# --- webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)

        if not update or not update.message:
            return "ok"

        chat_id = update.message.chat.id
        text = update.message.text or ""

        print("MESSAGE:", text)

        if text == "/start":
            start(chat_id)

        elif text == "/help":
            help_cmd(chat_id)

        elif is_tiktok(text):
            bot.send_message(chat_id, "⏳ Скачиваю...")

            video = download_video(text)

            if video:
                bot.send_video(chat_id, video)
            else:
                bot.send_message(chat_id, "❌ Не удалось скачать видео")

        else:
            bot.send_message(chat_id, "📌 Отправь TikTok ссылку")

        return "ok"

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "error"


# --- health check ---
@app.route("/")
def home():
    return "🤖 TikTokSaver bot is running"


# --- запуск ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("RUNNING ON PORT:", port)
    app.run(host="0.0.0.0", port=port)
