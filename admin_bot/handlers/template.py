from aiogram import Dispatcher, types

async def add_template(message: types.Message):
    await message.answer("Додавання шаблону...")

async def edit_template(message: types.Message):
    await message.answer("Редагування шаблону...")

async def delete_template(message: types.Message):
    await message.answer("Видалення шаблону...")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(add_template, commands=["add_template"])
    dp.register_message_handler(edit_template, commands=["edit_template"])
    dp.register_message_handler(delete_template, commands=["delete_template"])
