import os
import requests
from flask import Flask, request
from telegram import Bot, Update

# токен из переменной окружения
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)

app = Flask(__name__)

# --- логика ---
def is_tiktok(url):
    return "tiktok.com" in url

def download_video(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api, timeout=10).json()

        if r.get("data") and r["data"].get("play"):
            return r["data"]["play"]

        return None
    except:
        return None


# --- команды ---
def start(chat_id):
    bot.send_message(chat_id, "👋 Отправь TikTok ссылку 📥")

def help_cmd(chat_id):
    bot.send_message(chat_id,
        "📌 Как пользоваться ботом:\n\n"
        "1. Отправь ссылку на TikTok\n"
        "2. Бот скачает видео\n"
        "3. И пришлёт тебе 📥\n\n"
        "/start - запуск\n"
        "/help - помощь"
    )


# --- webhook ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)

    if update.message:
        chat_id = update.message.chat.id
        text = update.message.text or ""

        if text == "/start":
            start(chat_id)

        elif text == "/help":
            help_cmd(chat_id)

        else:
            if is_tiktok(text):
                bot.send_message(chat_id, "⏳ Скачиваю...")

                video = download_video(text)

                if video:
                    bot.send_video(chat_id, video)
                else:
                    bot.send_message(chat_id, "❌ Не удалось скачать видео")
            else:
                bot.send_message(chat_id, "📌 Это не TikTok ссылка")

    return "ok"


@app.route("/")
def home():
    return "🤖 TikTokSaver bot is running"


# --- запуск ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
