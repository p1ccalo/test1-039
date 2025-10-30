import logging
import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("BASE_URL")  # например: https://abcd1234.ngrok.io
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=storage)

# --- handlers ---
from handlers.start import register_handlers_start
register_handlers_start(dp)
from admin_bot.handlers.start import register_handlers as register_handlers_admin_start
register_handlers_admin_start(dp)
from admin_bot.handlers.new_client import register_handlers as register_handlers_new_client
register_handlers_new_client(dp)
from admin_bot.handlers.client import register_handlers as register_handlers_client
register_handlers_client(dp)

# --- webhook routes ---
async def handle_webhook(request):
    update = await request.json()
    from aiogram.types import Update
    upd = Update(**update)
    await dp.feed_update(upd)
    return web.Response()

async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set to {WEBHOOK_URL}")

async def on_shutdown():
    logger.info("Shutting down..")
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Bot closed.")

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)

async def main():
    await on_startup()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    logger.info(f"Webhook server started at {WEBAPP_HOST}:{WEBAPP_PORT}")
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
