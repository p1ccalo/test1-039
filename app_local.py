import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web
from dotenv import load_dotenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage


load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("BASE_URL")  # наприклад: https://abcd1234.ngrok.io
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"    # можна зробити будь-який унікальний шлях
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Якщо запускаєте локально на порті 8080, в ngrok будете пробросити порт 8080
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- handlers ---
# 👉 реєструємо всі хендлери
from handlers.start import register_handlers_start
register_handlers_start(dp)
from admin_bot.handlers.start import register_handlers
register_handlers(dp)
from admin_bot.handlers.new_client import register_handlers
register_handlers(dp)
from admin_bot.handlers.client import register_handlers
register_handlers(dp)


# --- webhook server (aiohttp) ---
async def on_startup(dp):
    # встановити webhook у Telegram
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set to {WEBHOOK_URL}")

async def on_shutdown(dp):
    logger.info("Shutting down..")
    await bot.delete_webhook()
    await bot.close()
    logger.info("Bot closed.")

if __name__ == "__main__":
    # запускаємо aiogram через start_webhook (використовує aiohttp під капотом)
    # webhook_path має відповідати шляху, який Telegram викликає (WEBHOOK_PATH)
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
