from aiogram import Dispatcher, types

async def view_all(message: types.Message):
    await message.answer("Перегляд даних...")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(view_all, commands=["view_all"])
