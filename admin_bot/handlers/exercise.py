from aiogram import Dispatcher, types
from backend.models import Exercise, Course, ExercisePhoto
from admin_bot.keyboards.keyboards import back_btn, exercise_edit_kb

from aiogram.dispatcher import FSMContext
from backend.db import SessionLocal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from admin_bot.states.states import EditExerciseStates
import os
from config import EXERCISE_PHOTOS_DIR

import dotenv
dotenv.load_dotenv()


async def add_exercise(message: types.Message):
    await message.answer("Додавання вправи...")

async def edit_exercise(call: types.CallbackQuery, state: FSMContext):
    print('call.data: ', call.data)
    exercise_id = call.data.split(":")[-1]
    print('exercise_id: ', exercise_id)
    db = SessionLocal()
    exercise = db.query(Exercise).get(exercise_id)
    kb = exercise_edit_kb(ex_id=exercise_id)
    text = f'✏️ Редагування вправи "{exercise.name}"\n\n'
    text += exercise.description
    print('exercise.photos: ', exercise.photos)
    if exercise.photos:
        if len(exercise.photos) == 1:
            photo_path=f'{EXERCISE_PHOTOS_DIR}/{exercise.photos[0].photo_url}.jpg'
            print('photo_path: ', photo_path)
            if os.path.exists(photo_path):
                photo = types.InputFile(photo_path)
                return await call.message.answer_photo(photo=photo, caption=text, reply_markup=kb)
            else:
                print('photo_path не існує')
        else:
            media = []
            for photo in exercise.photos:
                photo_path = f'{EXERCISE_PHOTOS_DIR}/{photo.photo_url}.jpg'
                if os.path.exists(photo_path):
                    media.append(types.InputMediaPhoto(media=types.InputFile(path=photo_path)))
            await call.message.answer_media_group(media=media)
            await call.message.answer(text, reply_markup=kb)
            return
    db.close()
    await call.message.edit_text(text, reply_markup=kb)

async def delete_exercise(call: types.CallbackQuery, state: FSMContext):
    exercise_id = call.data.split(":")[-1]
    db = SessionLocal()
    exercise = db.query(Exercise).get(exercise_id)
    course_id = exercise.course_id
    db.delete(exercise)
    db.commit()
    text = "✅ Вправа видалена!"
    await call.message.edit_text(text, reply_markup=back_btn(f"exercises:{course_id}"))
    db.close()
    


async def list_courses(message: types.Message, state: FSMContext):
    courses = SessionLocal().query(Course).all()
    text = 'Виберіть курс:\n\n'
    kb = InlineKeyboardMarkup(row_width=2)

    for course in courses:
        kb.insert(InlineKeyboardButton(text=course.name, callback_data=f"exercises:{course.id}"))
    await message.answer(text, reply_markup=kb)

async def list_exercises(callback: types.CallbackQuery):
    course_id = int(callback.data.split(":")[-1])
    exercises = SessionLocal().query(Exercise).filter(Exercise.course_id == course_id).all()
    text = 'Виберіть вправу:\n\n'
    kb = InlineKeyboardMarkup(row_width=2)

    for ex in exercises:
        kb.insert(InlineKeyboardButton(text=ex.name, callback_data=f"edit_exercise:{ex.id}"))
    await callback.message.edit_text(text, reply_markup=kb)


async def exercise_edit_name(callback: types.CallbackQuery, state: FSMContext):
    print('callback.data: ', callback.data)
    exercise_id = int(callback.data.split(":")[-1])
    exercise = SessionLocal().query(Exercise).get(exercise_id)
    text = f'✏️ Введіть нову назву для вправи "{exercise.name}"'
    await state.update_data(exercise_id=exercise_id)
    await EditExerciseStates.edit_name.set()
    await callback.message.edit_text(text, reply_markup=back_btn(f"edit_exercise:{exercise_id}"))


async def exercise_save_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    exercise_id = int(data.get("exercise_id"))
    db = SessionLocal()
    exercise = db.query(Exercise).get(exercise_id)
    exercise.name = message.text
    db.commit()
    text = f'✅ Назва вправи "{message.text}" змінена'
    print('exercise_id: ', exercise_id)
    await message.answer(text, reply_markup=back_btn(f"edit_exercise:{exercise_id}"))
    await state.finish()
    db.close()


async def add_exercise_photo(callback: types.CallbackQuery, state: FSMContext):
    exercise_id = int(callback.data.split(":")[-1])
    exercise = SessionLocal().query(Exercise).get(exercise_id)
    text = f'✏️ Надійшліть фотографію для вправи "{exercise.name}"'
    await state.update_data(exercise_id=exercise_id)
    await EditExerciseStates.photos.set()
    await callback.message.edit_text(text, reply_markup=back_btn(f"edit_exercise:{exercise_id}"))


async def exercise_edit_photo(callback: types.CallbackQuery, state: FSMContext):
    exercise_id = int(callback.data.split(":")[-1])
    exercise = SessionLocal().query(Exercise).get(exercise_id)
    text = f'✏️ Надійшліть фотографію для вправи "{exercise.name}"'
    await state.update_data(exercise_id=exercise_id)
    await EditExerciseStates.photos.set()
    if callback.message.photo:
        return await callback.message.edit_caption(text, reply_markup=back_btn(f"edit_exercise:{exercise_id}"))
    await callback.message.edit_text(text, reply_markup=back_btn(f"edit_exercise:{exercise_id}"))


async def exercise_edit_photo_save(message: types.Message, state: FSMContext):
    from backend.utils import save_exercise_photos
    data = await state.get_data()
    exercise_id = int(data.get("exercise_id"))
    db = SessionLocal()
    exercise = db.query(Exercise).get(exercise_id)
    exercise_photo = ExercisePhoto(exercise_id=exercise_id, photo_url=message.photo[0].file_unique_id)
    db.add(exercise_photo)
    db.commit()

    await save_exercise_photos(exercise_id, message)
    
    text = f'✅ Фотографія вправи "{exercise.name}" змінена'
    await message.answer(text, reply_markup=back_btn(f"edit_exercise:{exercise_id}"))
    await state.finish()
    db.close()








def register_handlers(dp: Dispatcher):
    dp.register_message_handler(add_exercise, commands=["add_exercise"])
    dp.register_callback_query_handler(edit_exercise, lambda c: c.data.startswith("edit_exercise:"), state='*')
    dp.register_callback_query_handler(delete_exercise, lambda c: c.data.startswith("delete_exercise:"))
    dp.register_message_handler(list_courses, lambda m: m.text == '🏷 Вправи', state='*')
    dp.register_callback_query_handler(list_exercises, lambda c: c.data.startswith("exercises:"))
    dp.register_callback_query_handler(exercise_edit_name, lambda c: c.data.startswith("exercise_edit_name:"))
    dp.register_message_handler(exercise_save_name, state=EditExerciseStates.edit_name)
    dp.register_callback_query_handler(add_exercise_photo, lambda c: c.data.startswith("add_exercise_photo:"))
    dp.register_callback_query_handler(exercise_edit_photo, lambda c: c.data.startswith("exercise_edit_photo:"))
    dp.register_message_handler(exercise_edit_photo_save, content_types=['photo'], state=EditExerciseStates.photos)