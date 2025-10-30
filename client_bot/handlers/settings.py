
from aiogram import types, Dispatcher

async def msg_settings(message: types.Message):
    await message.answer('''⚙️ Налаштування (демо):
— Ім’я/телефон/email змінюються наразі через реабілітолога.''')

def register_settings(dp: Dispatcher):
    dp.register_message_handler(msg_settings, lambda m: m.text == '⚙️ Налаштування')
