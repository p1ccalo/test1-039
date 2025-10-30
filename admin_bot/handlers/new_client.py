from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from datetime import datetime

from backend.db import SessionLocal
from backend.models import Client, User, ClientPhoto
from admin_bot.states.add_client import AddClient, STATE_TITLES
import os
import dotenv
from config import CLIENT_PHOTOS_DIR as client_photos_dir

dotenv.load_dotenv()
userbot_username = os.getenv("USERBOT_USERNAME")



# --- 🔸 Кнопка Назад ---
def back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
    )


# --- 🔸 Отримати унікальні відповіді з БД ---
def get_unique_answers(field_name: str):
    with SessionLocal() as db:
        answers = (
            db.query(getattr(Client, field_name))
            .filter(getattr(Client, field_name).isnot(None))
            .distinct()
            .all()
        )
        print(f"answers: {answers}")

        return answers


# --- 🔸 Клавіатура з унікальних минулих відповідей ---
def generate_keyboard(field_name: str):
    buttons = []
    if field_name not in ['name', 'birth_date', 'symptoms', 'symptoms_where', 'symptoms_how_long', 'symptoms_pain_level', 'blood_pressure', 'photos']: 
        buttons = [
            [InlineKeyboardButton(text=a[0], callback_data=f"answer:{a[0]}")]
            for a in get_unique_answers(field_name)
        ]
        print(f"buttons: {buttons}")
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons, row_width=2)


async def process_birth_date(message: types.Message, state: FSMContext):
    # Якщо поточне поле — дата народження
    text = message.text.strip()

    birth_date = None
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            birth_date = datetime.strptime(text, fmt).date()
            age = datetime.now().year - birth_date.year
            date = await state.get_data()
            client_id = int(date.get("client_id"))
            db = SessionLocal()
            client = db.query(Client).get(client_id)
            client.age = age
            db.commit()
            db.close()
            await message.answer("Вік: " + str(age))
            break
        except ValueError:
            continue

    if not birth_date:
        await message.answer("⚠️ Введіть дату у форматі 29.03.1990 або 29.03.90")
        return

    return birth_date



# --- 🔹 Початок опитування ---
async def add_client_start(message: types.Message, state: FSMContext):
    await state.finish()
    await state.set_state(AddClient.name.state)
    await message.answer("Введіть ім'я клієнта:")


# --- 🔹 Обробка текстових відповідей ---
async def process_field(message: types.Message, state: FSMContext):
    print('message.text: ', message.text)
    state_name = (await state.get_state()).split(":")[1]
    value = message.text

    if state_name == "birth_date":
        value = await process_birth_date(message, state)
    elif state_name == "photos":
        return

    print(f"state_name: {state_name}, value: {value}")
    data = await state.get_data()
    client_id = data.get("client_id")
    print('client_id: ', client_id)
    if not client_id:
        with SessionLocal() as db:
            client = Client()
            db.add(client)
            try:
                setattr(client, state_name, value)
            except Exception as e:
                print(f"⚠️ Не вдалося записати {state_name}: {e}")
            db.commit()
            db.refresh(client)
            print('new client has been created: ', client)
            await state.update_data(client_id=client.id)
    else:
        with SessionLocal() as db:
            client = db.query(Client).get(client_id)
            print('client: ', client.name)
            try:
                setattr(client, state_name, value)
            except Exception as e:
                print(f"⚠️ Не вдалося записати {state_name}: {e}")
            db.commit()
            db.refresh(client)
            print('client has been updated: ', client)

    next_state = get_next_state(state_name)
    print('next_state: ', next_state)
    if next_state:
        await state.set_state(getattr(AddClient, next_state))
        if next_state == "photos":
            text = "📸 Додайте фото або натисніть кнопку готово"
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("Готово", callback_data="done_photos"))
            return await message.answer(text, reply_markup=kb)
        await message.answer(
            f"Введіть {STATE_TITLES.get(next_state, next_state)}:",
            reply_markup=generate_keyboard(next_state)
        )
    else:
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("Переглянути", callback_data=f"client:{client_id}"))
        await message.answer("✅ Опитування завершено!", reply_markup=kb)
        await state.finish()
    db.close()


# --- 🔹 Обробка вибору готової відповіді ---
async def choose_past_answers(call: types.CallbackQuery, state: FSMContext):
    value = call.data.split(":", 1)[1]
    print('past answer: ', value)
    state_name = (await state.get_state()).split(":")[1]
    db = SessionLocal()
    data = await state.get_data()
    client_id = data.get("client_id")
    client = db.query(Client).get(client_id)
    setattr(client, state_name, value)
    db.commit()
    db.close()

    next_state = get_next_state(state_name)
    print('next_state: ', next_state)
    if next_state:
        await state.set_state(next_state)
        await call.message.answer(
            f"Введіть {STATE_TITLES.get(next_state, next_state)}:",
            reply_markup=generate_keyboard(next_state)
        )
    else:
        await call.message.answer("✅ Опитування завершено!")
        await state.finish()


# --- 🔹 Обробка кнопки Назад ---
async def go_back(call: types.CallbackQuery, state: FSMContext):
    current_state = (await state.get_state()).split(":")[1]
    prev_state = get_prev_state(current_state)
    if not prev_state:
        await call.answer("Це початок опитування.")
        return

    await state.set_state(prev_state)
    await call.message.edit_text(
        f"Введіть {prev_state}:",
        reply_markup=generate_keyboard(prev_state)
    )


# --- 🔸 Визначення наступного/попереднього стану ---
def get_all_states():
    return [s.state.split(":")[1] for s in AddClient.__dict__.values() if hasattr(s, "state")]


def get_next_state(current_state):
    states = get_all_states()
    idx = states.index(current_state)
    return states[idx + 1] if idx + 1 < len(states) else None


def get_prev_state(current_state):
    states = get_all_states()
    idx = states.index(current_state)
    return states[idx - 1] if idx > 0 else None


async def add_new_client_photos(message: types.Message, state: FSMContext):
    # Кнопка "Готово" для фото
    done_kb = InlineKeyboardMarkup(row_width=1)
    if message.photo:
        client_id = (await state.get_data()).get("client_id")
        db = SessionLocal()
        os.makedirs(client_photos_dir, exist_ok=True)

        photo_id = message.photo[-1].file_id
        print('photo_id: ', photo_id)
        file = await message.bot.get_file(photo_id)
        file_path = os.path.join(client_photos_dir, f"{photo_id}.jpg")

        # Завантажуємо файл
        await message.bot.download_file(file.file_path, file_path)
        print('file_path: ', file_path)

        # Зберігаємо шлях у базу
        client_photo = ClientPhoto(client_id=client_id, photo_url=photo_id)
        db.add(client_photo)    
        db.commit()
        done_kb.add(InlineKeyboardButton("✅ Готово", callback_data="done_photos"))
        text="Фото збережено.\n\nНадішліть ще фото або натисніть 'Готово'"
        await message.answer(text, reply_markup=done_kb)
    else:
        await message.answer("Файл не схожий на фото.\n\nНадішліть фото клієнта або натисніть 'Готово'", reply_markup=done_kb)
    await AddClient.photos.set()
    db.close()


async def add_new_client_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("Переглянути", callback_data=f"client:{client_id}"))
    await callback_query.message.answer("✅ Клієнт створений.", reply_markup=kb)
    await state.finish()




# --- 🔹 Реєстрація хендлерів ---
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(add_client_start, lambda m: m.text == '➕ Додати клієнта', state='*')
    dp.register_message_handler(add_new_client_photos, content_types=['photo'], state=AddClient.photos)
    dp.register_message_handler(process_field, state=AddClient)
    dp.register_callback_query_handler(choose_past_answers, lambda c: c.data.startswith("answer:"), state=AddClient)
    dp.register_callback_query_handler(go_back, lambda c: c.data.startswith("back:"), state=AddClient)
    dp.register_callback_query_handler(add_new_client_confirm, lambda c: c.data.startswith("done_photos"), state=AddClient.photos)
