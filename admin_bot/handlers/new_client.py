from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import joinedload, Session
from datetime import datetime
from typing import Union
from backend.db import SessionLocal
from backend.models import Client, User, ClientPhoto
from admin_bot.states.add_client import AddClient, STATE_TITLES
import os
import dotenv
from config import CLIENT_PHOTOS_DIR as client_photos_dir
from .client import client_card_text
from aiogram import Bot

bot = Bot.get_current()

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
async def generate_keyboard(field_name: str, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_values", [])

    buttons = []

    from admin_bot.states.add_client import STATE_QUESTION_TYPES
    field_question_type = STATE_QUESTION_TYPES.get(field_name, None)


    if field_question_type == "multi":
        answers = get_unique_answers(field_name)
        answer_map = {i: a[0] for i, a in enumerate(answers)}
        await state.update_data(answer_map=answer_map)

        for i, text in answer_map.items():
            # позначаємо вибрані кнопки
            prefix = "✅ " if text in selected else ""
            buttons.append([
                InlineKeyboardButton(
                    text=f"{prefix}{text}",
                    callback_data=f"multi:{field_name}:{i}"
                )
            ])

    # кнопка далі
    buttons.append([InlineKeyboardButton("➡️ Далі", callback_data=f"next:{field_name}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def choose_multi(call: types.CallbackQuery, state: FSMContext):
    _, field_name, idx = call.data.split(":")
    data = await state.get_data()
    answer_map = data["answer_map"]
    value = answer_map[int(idx)]
    selected = data.get("selected_values", [])

    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)

    print("selected", selected)
    await state.update_data(selected_values=selected)

    # оновлюємо клавіатуру з відмітками ✅
    kb = await generate_keyboard(field_name, state)
    await call.message.edit_reply_markup(reply_markup=kb)



async def process_birth_date(client_id: int, birth_date_text: str):
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            birth_date = datetime.strptime(birth_date_text, fmt).date()
            age = datetime.now().year - birth_date.year
            db = SessionLocal()
            client = db.query(Client).get(client_id)
            client.age = age
            db.commit()
            db.close()
            break 
        except ValueError:
            continue

    return birth_date



# --- 🔹 Початок опитування ---
async def add_client_start(message: types.Message, state: FSMContext):
    await state.finish()
    await state.set_state(AddClient.name.state)
    card = await message.answer("🧾 Картка клієнта:\n(поки що порожня)")
    question = await message.answer("Введіть ім’я клієнта:")
    await state.update_data(card_message_id=card.message_id, question_message_id=question.message_id)


async def process_field(message: types.Message, state: FSMContext):
    await answer_func(message, state)


async def client_update(client_id: int, state_name, value):
    db = SessionLocal()
    client = db.query(Client).get(client_id)

    try:
        # Якщо поле підтримує кілька виборів — зберігаємо список
        if isinstance(value, list):
            setattr(client, state_name, ", ".join(value))
        else:
            setattr(client, state_name, value)

        db.commit()
        db.refresh(client)
    except Exception as e:
        print(f"⚠️ Не вдалося оновити {state_name}: {e}")
    finally:
        db.close()

    return client


async def client_create(name: str):
    db: Session = SessionLocal()
    client = Client(name=name)
    db.add(client)
    db.commit()
    db.refresh(client)
    client_id = client.id
    db.close()
    return client_id


# === 🔹 Основна функція для оновлення картки та переходу далі ===
async def answer_func(event: Union[types.Message, types.CallbackQuery], state: FSMContext):
    """
    Оновлює картку клієнта після відповіді (текст/кнопка),
    зберігає зміни та переходить до наступного питання.
    """
    message = None
    if isinstance(event, types.CallbackQuery):
        message = event.message
        value = event.data.split(":", 1)[1]
    else:
        message = event
        value = message.text.strip()


    state_name = (await state.get_state()).split(":")[1]
    data = await state.get_data()
    client_id = data.get("client_id")
    card_message_id = data.get("card_message_id")
    question_message_id = data.get("question_message_id")
    print('client_id: ', client_id)
    print('state_name: ', state_name)
    print('value: ', value)
    print('card_message_id: ', card_message_id)
    print('question_message_id: ', question_message_id)

    # --- 1️⃣ Отримуємо клієнта ---
    if client_id is None:
        client_id = await client_create(name=value)
        print('client_id: ', client_id)
        await state.update_data(client_id=client_id)


    # --- 2️⃣ Оновлюємо відповідь ---
    if state_name == "birth_date":
        value = await process_birth_date(client_id, value)
    client = await client_update(client_id, state_name, value)
    print('client name:', client.name)
    await generate_next_question(message, state)
        

async def generate_next_question(message: types.Message, state: FSMContext):
    state_name = (await state.get_state()).split(":")[1]
    data = await state.get_data()
    client_id = data.get("client_id")
    card_message_id = data.get("card_message_id")
    question_message_id = data.get("question_message_id")
    client = SessionLocal().query(Client).get(client_id)
        # --- 3️⃣ Оновлюємо картку клієнта ---
    client_text = client_card_text(client)
    await bot.delete_message(chat_id=message.chat.id, message_id=card_message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=question_message_id)
    card = await message.answer(client_text)
    await state.update_data(card_message_id=card.message_id)

    # --- 4️⃣ Наступне питання ---
    next_state = get_next_state(state_name)
    print('next_state: ', next_state)
    if next_state:
        await state.set_state(getattr(AddClient, next_state))
        if next_state == "photo":
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("Готово", callback_data=f"done_photos"))
            await message.answer("Завантажте фото або натисніть \"Готово\"", reply_markup=kb)
        else:
            kb = await generate_keyboard(next_state, state)
            question = await message.answer(
                f"Введіть {STATE_TITLES.get(next_state, next_state)}:",
                reply_markup=kb
            )
        await state.update_data(question_message_id=question.message_id)
    else:
        # --- 5️⃣ Завершення ---
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("Переглянути", callback_data=f"client:{client_id}"))
        await message.answer("✅ Опитування завершено!", reply_markup=kb)
        await state.clear()


async def next_question(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_values = data.get("selected_values")
    state_name = (await state.get_state()).split(":")[1]
    client_id = data.get("client_id")
    
    if selected_values:
        print('selected_values: ', selected_values)
        await client_update(client_id, state_name, selected_values)

    await state.update_data(selected_values=[])
    await generate_next_question(call.message, state)





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
        reply_markup= await generate_keyboard(prev_state, state)
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

    dp.register_callback_query_handler(next_question, lambda c: c.data.startswith("next:"), state=AddClient)
    dp.register_callback_query_handler(choose_multi, lambda c: c.data.startswith("multi:"), state=AddClient)
    dp.register_callback_query_handler(go_back, lambda c: c.data.startswith("back:"), state=AddClient)
    dp.register_callback_query_handler(add_new_client_confirm, lambda c: c.data.startswith("done_photos"), state=AddClient.photos)