import logging
import os
from aiogram import Bot, Dispatcher, types
from aiohttp import web
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 8080  # пробросимо цей порт через ngrok
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
bot.set_current(bot)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- хендлери ---
from handlers.start import register_handlers_start
register_handlers_start(dp)

# --- webhook handlers ---
async def handle_webhook(request):
    try:
        data = await request.json()
        bot.set_current(bot)
        try:
            update = types.Update(**data)
        except TypeError:
            update = types.Update.de_json(data)

        await dp.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return web.Response(status=200)

# --- root ---
async def handle_root(request):
    return web.Response(text="Bot running locally ✅")

# --- main ---
app = web.Application()
app.router.add_get("/", handle_root)
app.router.add_post(WEBHOOK_PATH, handle_webhook)

if __name__ == "__main__":
    logger.info(f"Local server running at http://{WEBAPP_HOST}:{WEBAPP_PORT}")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
