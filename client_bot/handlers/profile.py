
from aiogram import types, Dispatcher
from backend.utils import get_client_by_tg
import os
from dotenv import load_dotenv
from client_bot.keyboards import back_kb

load_dotenv()

CLIENT_PHOTOS_DIR = os.getenv('CLIENT_PHOTOS_DIR')

# import get_client_by_tg

def _fmt(val):
    return val if val else '—'

async def msg_profile(message: types.Message):
    user_key = str(message.from_user.id)  # можна використати username: message.from_user.username
    data = get_client_by_tg(user_key) or get_client_by_tg(message.from_user.username or '')
    if not data:
        return await message.answer('Профіль не знайдено. Зверніться до реабілітолога.')
    text = (
        f"👤 Профіль\n\n"
        f"Ім’я: {_fmt(data.name)}\n"
        f"Вік: {_fmt(data.age)}\n"
        f"Симптоми: {_fmt(data.symptoms)}\n"
        f"Що робить: {_fmt(data.activities)}\n"
        f"Результати дослідження: {_fmt(data.research_results)}\n"
        f"Рекомендації з масажу: {_fmt(data.massage_recommendations)}\n\n"
        f"Посилання для запрошення друзів: https://t.me/{os.getenv('USERBOT_USERNAME')}?start=ref_{data.id}\n\n"
    )
    kb = types.InlineKeyboardMarkup()
    text += f"Програми: {len(data.programs)}\n"
    if data.programs:
        for program in data.programs:
            text += f"- {program.course.name}\n"
        kb.add(types.InlineKeyboardButton(text='Мої програми', callback_data=f'client_programs:{data.id}'))

            
                
    if data.photos:
        if len(data.photos) == 1:
            photo_url=f'{CLIENT_PHOTOS_DIR}/{data.photos[0].photo_url}.jpg'
            if os.path.exists(photo_url):
                photo=types.InputFile(photo_url)
            await message.answer_photo(photo=photo, caption=text, reply_markup=kb)
        else:
            media=[]
            for photo in data.photos:
                photo_path=f'{CLIENT_PHOTOS_DIR}/{photo.photo_url}.jpg'
                if os.path.exists(photo_path):
                    media.append(types.InputMediaPhoto(media=types.InputFile(photo_path)))
            await message.answer_media_group(media=media)
            await message.answer(text, reply_markup=kb)
    else:    
        await message.answer(text, reply_markup=kb)

def register_profile(dp: Dispatcher):
    dp.register_message_handler(msg_profile, lambda m: m.text == '👤 Мій профіль')
