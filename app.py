import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web
from dotenv import load_dotenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
import sys
from backend.db import init_db


load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("BASE_URL")  # наприклад: https://abcd1234.ngrok.io
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"    # можна зробити будь-який унікальний шлях
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Якщо запускаєте локально на порті 8080, в ngrok будете пробросити порт 8080
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
Bot.set_current(bot)  # <- ось це ключове
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
from admin_bot.handlers.view import register_handlers
register_handlers(dp)
from admin_bot.handlers.template import register_handlers
register_handlers(dp)
from admin_bot.handlers.exercise import register_handlers
register_handlers(dp)
from admin_bot.handlers.program import register_handlers
register_handlers(dp)

from client_bot.handlers.program import register_program
register_program(dp)
from client_bot.handlers.common import register_common
register_common(dp)
from client_bot.handlers.profile import register_profile
register_profile(dp)
from client_bot.handlers.products import register_products
register_products(dp)
from client_bot.handlers.services import register_services
register_services(dp)
from client_bot.handlers.settings import register_settings
register_settings(dp)
from client_bot.handlers.start_session import register_handlers
register_handlers(dp)
from client_bot.handlers.client import register_handlers_client
register_handlers_client(dp)


# --- webhook server (aiohttp) ---
async def on_startup(dp):
    # встановити webhook у Telegram
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set to {WEBHOOK_URL}")

async def on_shutdown(dp):
    logger.info("Shutting down..")
    await bot.delete_webhook()
    logger.info("Bot closed.")

# --- ✅ Додаємо маршрут для GET / ---
async def healthcheck(request):
    return web.Response(text="✅ Bot is running", content_type="text/plain")

async def handle_webhook(request):
    """POST /webhook — сюди Telegram шле апдейти"""
    try:
        data = await request.json()
        update = types.Update(**data)
        Dispatcher.set_current(dp)  # <- обов'язково для FSM
        await dp.process_update(update)
    except Exception as e:
        logging.exception("Webhook error: %s", e)
    return web.Response(status=200)


# === Основна точка входу ===
# --- app ---
app = web.Application()
app.router.add_get("/", healthcheck)
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
# app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    # Ініціалізуємо базу даних перед запуском
    init_db()
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)