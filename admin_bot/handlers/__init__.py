from aiogram import Dispatcher
from admin_bot.handlers.add_client import router as add_client_router

dp = Dispatcher()
dp.include_router(add_client_router)
