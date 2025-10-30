from aiogram import types
from backend.services.client_message import build_client_message

async def send_client_info(message: types.Message):
    client_id = 19  # наприклад, тестово
    text, photo, kb = build_client_message(client_id)

    if photo:
        await message.answer_photo(photo=photo, caption=text, reply_markup=kb)
    else:
        await message.answer(text=text, reply_markup=kb)


def register_handlers_client(dp):
    dp.register_message_handler(send_client_info, commands=['client'])