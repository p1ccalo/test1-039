from aiogram import types, Dispatcher
from client_bot.keyboards import main_menu
from backend.utils import get_client_by_tg, get_client_program_exercises
import datetime
from backend.models import Exercise, Client
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

user_sessions={}

async def msg_start_session(message: types.Message):
    client = get_client_by_tg(message.from_user.id)
    exercises = get_client_program_exercises(client.id, 1)

    if not exercises:
        await message.answer("⚠️ Вам ще не призначено жодної програми.")
        return

    # Створюємо сесію
    user_sessions[client.id] = {
        "exercises": exercises,
        "current": 0,
        "start_time": datetime.datetime.now()
    }

    await send_exercise(message, exercises[0], 1, len(exercises))


async def send_exercise(message: types.Message, exercise: Exercise, index: int, total: int):
    """Надсилає вправу з кнопкою"""
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Закінчити вправу", callback_data="finish_exercise")
    )

    text = f"🏋️‍♂️ Вправа {index}/{total}\n\n<b>{exercise.name}</b>\n\n{exercise.description}"

    if exercise.media_url:
        await message.answer_photo(
            exercise.media_url,
            caption=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=kb,
            parse_mode="HTML"
        )



async def finish_exercise(callback: types.CallbackQuery):
    client = get_client_by_tg(callback.from_user.id)
    user_id = client.id

    if user_id not in user_sessions:
        await callback.answer("⚠️ Почніть заняття командою /start_session")
        return

    session_data = user_sessions[user_id]
    session_data["current"] += 1
    current = session_data["current"]
    total = len(session_data["exercises"])

    if current < total:
        await callback.message.answer(f"✅ Виконана {current} вправа з {total}")
        await send_exercise(callback.message, session_data["exercises"][current], current + 1, total)
    else:
        duration = datetime.datetime.now() - session_data["start_time"]
        minutes, seconds = divmod(duration.seconds, 60)
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Отримати Щасливі", callback_data="get_happies")
        )
        await callback.message.answer(
            f"🎉 Вітаємо! Ви виконали всі {total} вправ!\n"
            f"⏱ Час заняття: {minutes} хв {seconds} сек"
            f"Отримайте 10 Щасливих. Натисніть кнопку нижче",
            reply_markup=kb
        )
        del user_sessions[user_id]  # Скидаємо сесію

async def msg_get_happie(callback: types.CallbackQuery):
    client = get_client_by_tg(callback.from_user.id)
    client.happies += 10
    await callback.message.answer("✅ Отримано 10 Щасливих. Всього Щасливих: " + str(client.happies))
    

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(msg_start_session, lambda m: m.text == "🏋️‍♂️ Почати заняття")
    dp.register_callback_query_handler(finish_exercise, lambda c: c.data == "finish_exercise")
    dp.register_callback_query_handler(msg_get_happie, lambda c: c.data == "get_happies")