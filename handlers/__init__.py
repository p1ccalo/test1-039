from .start import start
from aiogram import Dispatcher


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'])