
from aiogram import types, Dispatcher
from backend.utils import get_client_by_tg
import os
from dotenv import load_dotenv
from client_bot.keyboards import back_kb
from backend.models import User, Client
from backend.db import SessionLocal

load_dotenv()

CLIENT_PHOTOS_DIR = os.getenv('CLIENT_PHOTOS_DIR')

# import get_client_by_tg

def _fmt(val):
    return val if val else '—'


def profile_text(client: Client):
    text = f"👤 Ім'я: {client.name}\n"
    if client.birth_date:
        text += f"👦 Дата народження: {client.birth_date} (Вік: {client.age})\n"
    if client.symptoms:
        text += f"Симптоми:\n {client.symptoms}\n"
    if client.symptoms_where:
        text += f"Де турбує: {client.symptoms_where}\n"
    if client.symptoms_how_long:
        text += f"Як давно турбує: {client.symptoms_how_long}\n"
    if client.symptoms_pain_level:
        text += f"Рівень болю: {client.symptoms_pain_level}\n"
    if client.blood_pressure:
        text += f"Тиск: {client.blood_pressure}\n"
    if client.activities:
        text += f"🎯 Що робить: {client.activities}\n"
    
    if client.research_feet:
        text += f"\n🔬 Результати дослідження:\n"
        text += f"Стопи: {client.research_feet}\n"
    if client.research_knees:
        text += f"Коліна: {client.research_knees}\n"
    if client.research_pelvis:
        text += f"Таз: {client.research_pelvis}\n"
    if client.research_posture:
        text += f"Постава: {client.research_posture}\n"
    if client.func_back_thoracic:
        text += f"Спина тригері: - грудний відділ: {client.func_back_thoracic}\n"
    if client.func_back_lumbar:
        text += f"Спина тригері: - поперековий відділ: {client.func_back_lumbar}\n"
    if client.func_back_neck:
        text += f"Спина тригері: - шия: {client.func_back_neck}\n"
    if client.func_hips:
        text += f"Кульшові суглоби: {client.func_hips}\n"
    if client.func_knees:
        text += f"Колінні суглоби: {client.func_knees}\n"
    if client.func_ankles:
        text += f"Гомілковостопні суглоби: {client.func_ankles}\n"
    if client.func_feet:
        text += f"Стопи: {client.func_feet}\n"
    if client.func_symmetry:
        text += f"Симетрія нижніх кінцівок: {client.func_symmetry}\n"
    if client.func_shoulders:
        text += f"Плечі: {client.func_shoulders}\n"
    if client.func_elbows:
        text += f"Лікті: {client.func_elbows}\n"
    if client.func_wrists:
        text += f"Зап'ястя: {client.func_wrists}\n"
    if client.work_conditions:
        text += f"\nПобут / Спосіб життя:\n Умови роботи: {client.work_conditions}\n"
    if client.sport:
        text += f"Заняття спортом/фітнесом: {client.sport}\n"
    if client.supplements:
        text += f"Використання БАД у харчуванні: {client.supplements}\n"
    if client.home_devices:
        text += f"Використання запобіжних масажерів або тренажерів в домашніх умовах: {client.home_devices}\n"
    if client.conclusion:
        text += f"\nВисновки та рекомендації\n {client.conclusion}"

    return text



async def msg_profile(message: types.Message):
    user_key = str(message.from_user.id)  # можна використати username: message.from_user.username
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_key).first()
    data = user.client
    if not data:
        return await message.answer('Профіль не знайдено. Зверніться до реабілітолога.')
    text = profile_text(data)
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
    db.close()

def register_profile(dp: Dispatcher):
    dp.register_message_handler(msg_profile, lambda m: m.text == '👤 Мій профіль')