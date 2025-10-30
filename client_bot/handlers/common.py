
from aiogram import types, Dispatcher
from client_bot.keyboards import main_menu
from client_bot.texts import WELCOME, ABOUT, HELP, WELCOME_CLIENT
from backend.models import Client
from backend.db import SessionLocal
# from backend.utils import get_articles

async def cmd_start(message: types.Message):
    print('message.text: ', message.text)
    if ' ' in message.text:
        client_id = int(message.text.split(' ')[-1])
        print('client_id: ', client_id)
        db = SessionLocal()
        client = db.query(Client).get(client_id)
        if client:
            text = WELCOME_CLIENT.format(name=client.name)
            await message.answer(text, reply_markup=main_menu)
            client.telegram_id = message.from_user.id
            db.commit()
            print('client.telegram_id оновлено: ', client.telegram_id)
        else:
            await message.answer('Немає такого клієнта')
        db.close()
        return
    


    return await message.answer(WELCOME, reply_markup=main_menu)

async def msg_about(message: types.Message):
    await message.answer(ABOUT)

async def msg_help(message: types.Message):
    await message.answer(HELP)

async def msg_helpful(message: types.Message):
    return await message.answer('Поки що немає матеріалів.')
    # arts = get_articles()
    # if not arts:
    # text = '📚 Корисне\n\n' + '\n\n'.join([f"• {a['title']}\n{a['content'][:160]}{'...' if len(a['content'])>160 else ''}" for a in arts])
    # await message.answer(text)

def split_text_to_name_and_description(text: str):
    """Розділяє текст: перший рядок = назва, решта = опис"""
    if not text:
        return "Без назви", "Без опису"

    lines = text.strip().split("\n", 1)
    name = lines[0].strip()
    description = lines[1].strip() if len(lines) > 1 else ""
    return name, description

async def handle_forwarded_message(message: types.Message):
    # Перевіряємо, чи переслане повідомлення
    if message.forward_from or message.forward_from_chat:
        text = ''
        file_id = None
        # Якщо переслано фото
        if message.photo:
            
            photo = message.photo[-1]  # найбільший розмір
            file_id = photo.file_id
            text = message.caption if message.caption else "Без підпису"
        if message.text:
            text = message.text
        from backend.services.parse_message_client import parse_message_client
        client = parse_message_client(text, file_id)
        from backend.services.client_message import build_client_message
        text, photo, kb = build_client_message(client.id)
        if photo:
            await message.answer_photo(photo=photo, caption=text, reply_markup=kb)
        else:
            await message.answer(text=text, reply_markup=kb)



async def default_message(message: types.Message):
    print('message', message)
    if message.text:
        await message.answer(message.text)
    if message.photo:
        photo = message.photo[-1]  # найбільший розмір
        await message.answer_photo(photo.file_id)
            
    

def register_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(msg_about, lambda m: m.text == '🏥 Про Orthospin')
    dp.register_message_handler(msg_helpful, lambda m: m.text == 'ℹ️ Корисне')
    dp.register_message_handler(msg_help, lambda m: m.text == '❓ Допомога')
    dp.register_message_handler(handle_forwarded_message, lambda m: m.forward_from or m.forward_from_chat, content_types=types.ContentType.ANY)
    # dp.register_message_handler(default_message, content_types=types.ContentType.ANY)