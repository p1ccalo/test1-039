
from aiogram import types, Dispatcher
from backend.utils import get_client_by_tg
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from client_bot.keyboards import back_kb
from backend.db import SessionLocal
from backend.models import Program, Exercise
import os
import dotenv
from backend.models import User

dotenv.load_dotenv()
EXERCISE_PHOTOS_DIR = os.getenv('EXERCISE_PHOTOS_DIR')

async def msg_my_programs(message: types.Message):
    user_key = str(message.from_user.id)
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_key).first()
    client = user.client
    if not client:
        return await message.answer('Профіль не знайдено. Зверніться до реабілітолога.')
    progs = client.programs
    print('progs', progs)
    db.close()
    if not progs:
        return await message.answer('Програми поки не призначені.')
    if len(progs) > 1:
        text="📋 Мої програми\n\n"
        text += "Виберіть програму:\n\n"
        kb=InlineKeyboardMarkup(row_width=1)
        for prog in progs:
            kb.add(InlineKeyboardButton(text=prog.course.name, callback_data=f'program:{prog.id}'))
        return await message.answer(text, reply_markup=kb)
    else:
        prog = progs[0]
        text="📋 Моя програма\n\n"
        text += f'{prog.course.name}\n\n'
        kb=InlineKeyboardMarkup(row_width=1)
        for e in prog.exercises:
            text += f'- {e.exercise.name}\n'
            kb.add(InlineKeyboardButton(text=e.exercise.name, callback_data=f'program_exercise:{prog.id}_{e.exercise.id}'))
        return await message.answer(text, reply_markup=kb)
    

async def msg_program(callback: types.CallbackQuery):
    prog_id = int(callback.data.split(":")[1])
    prog = SessionLocal().query(Program).get(prog_id)
    text="📋 Моя програма\n\n"
    text += f'{prog.course.name}\n\n'
    kb=InlineKeyboardMarkup(row_width=1)
    for e in prog.exercises:
        text += f'- {e.exercise.name}\n'
        kb.add(InlineKeyboardButton(text=e.exercise.name, callback_data=f'program_exercise:{prog.id}_{e.exercise.id}'))
    await callback.message.edit_text(text, reply_markup=kb)


async def msg_program_exercise(callback: types.CallbackQuery):
    print('callback.data: ', callback.data)
    prog_ex_data = callback.data.split(":")[1]
    print('prog_ex_data: ', prog_ex_data)
    prog_id = int(prog_ex_data.split("_")[0])
    print('prog_id: ', prog_id)
    ex_id = int(prog_ex_data.split("_")[1])
    print('ex_id: ', ex_id)
    prog = SessionLocal().query(Program).get(prog_id)
    exercise = SessionLocal().query(Exercise).get(ex_id)
    text=f"Вправа: {exercise.name}\n\n"
    text += f'{exercise.description}\n\n'
    kb=InlineKeyboardMarkup(row_width=1)
    kb.add(back_kb(callback_data=f'program:{prog.id}'))
    if exercise.photos:
        if len(exercise.photos) == 1:
            photo_path=f'{EXERCISE_PHOTOS_DIR}/{exercise.photos[0].photo_url}.jpg'
            if os.path.exists(photo_path):
                photo = types.InputFile(path=photo_path)
                return await callback.message.answer_photo(photo=photo, caption=text, reply_markup=kb)
        else:
            media = []
            for photo in exercise.photos:
                photo_path = f'{EXERCISE_PHOTOS_DIR}/{photo.photo_url}.jpg'
                if os.path.exists(photo_path):
                    media.append(types.InputMediaPhoto(media=types.InputFile(path=photo_path)))
            await callback.message.answer_media_group(media=media)
            await callback.message.answer(text, reply_markup=kb)
            return
    await callback.message.edit_text(text, reply_markup=kb)

def register_program(dp: Dispatcher):
    dp.register_message_handler(msg_my_programs, lambda m: m.text == '📋 Мої програми')
    dp.register_callback_query_handler(msg_program, lambda c: c.data.startswith('program:'))
    dp.register_callback_query_handler(msg_program_exercise, lambda c: c.data.startswith('program_exercise:'))