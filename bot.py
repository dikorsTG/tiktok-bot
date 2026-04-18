import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# токен
import os
TOKEN = os.getenv("8738791326:AAFgYaGyeVE3fwl-Ttox67VEU7WTW3BNKfg")

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Отправь TikTok ссылку 📥")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Как пользоваться ботом:\n\n"
        "1. Отправь ссылку на TikTok\n"
        "2. Бот скачает видео\n"
        "3. И пришлёт его тебе 📥\n\n"
        "Команды:\n"
        "/start - запуск\n"
        "/help - помощь"
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if is_tiktok(text):
        await update.message.reply_text("⏳ Скачиваю...")

        video = download_video(text)

        if video:
            await update.message.reply_video(video)
        else:
            await update.message.reply_text("❌ Не удалось скачать видео")
    else:
        await update.message.reply_text("📌 Это не TikTok ссылка")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🤖 Бот запущен...")
app.run_polling()
