from aiogram import types, Dispatcher
from admin_bot.keyboards.keyboards import main_menu


async def cmd_start(message: types.Message):
    await message.answer('👋 Адмін-панель Orthospin', reply_markup=main_menu)


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'], state='*')