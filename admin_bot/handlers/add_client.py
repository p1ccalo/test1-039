# admin_bot/handlers/add_client.py
from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from backend.db import SessionLocal
from backend.models import Client
from admin_bot.states.add_client import AddClient
from admin_bot.handlers.client import client_card_text, client_actions_kb

# Вопросы для диалога
QUESTIONS = [
    {"key": "name", "text": "Введіть ім'я клієнта:", "multi": False},
    {"key": "birth_date", "text": "Введіть дату народження (YYYY-MM-DD):", "multi": False},
    {"key": "age", "text": "Введіть вік клієнта:", "multi": False},
    {"key": "symptoms", "text": "Введіть симптоми клієнта:", "multi": False},
    {"key": "activities", "text": "Що робить клієнт?", "multi": True, "options": ["Спорт", "Офісна робота", "Хобі", "Інше"]},
    {"key": "massage_recommendation", "text": "Рекомендації по масажу:", "multi": False}
]

# Кнопка "Далі"
def next_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Далі ➡️", callback_data="next_question"))
    return kb

# Начало диалога
async def start_add_client(message: types.Message, state: FSMContext):
    db = SessionLocal()
    client = Client(name="Новий клієнт")
    db.add(client)
    db.commit()
    db.refresh(client)
    db.close()

    await state.update_data(client_id=client.id, question_idx=0, answers={})

    await message.answer(client_card_text(client))

    question = QUESTIONS[0]
    await message.answer(question["text"])
    await AddClient.waiting_for_answer.set()

# Обработка текстового ответа
async def handle_text_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data["client_id"]
    question_idx = data["question_idx"]
    answers = data.get("answers", {})

    key = QUESTIONS[question_idx]["key"]
    answer = message.text.strip()

    # Сохраняем в стейт
    answers[key] = answer
    await state.update_data(answers=answers)

    # Сохраняем в базе
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    if key == "age":
        client.age = int(answer)
    elif key == "birth_date":
        from datetime import datetime
        try:
            client.birth_date = datetime.strptime(answer, "%Y-%m-%d").date()
        except:
            await message.answer("Неправильний формат дати. Спробуйте ще раз (YYYY-MM-DD):")
            db.close()
            return
    else:
        setattr(client, key, answer)
    db.commit()
    db.close()

    # Обновляем картку
    await message.edit_text(client_card_text(client))

    await next_question(message, state)

# Обработка нажатий кнопок
async def handle_option(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client_id = data["client_id"]
    question_idx = data["question_idx"]
    answers = data.get("answers", {})
    question = QUESTIONS[question_idx]

    if call.data == "next_question":
        await next_question(call.message, state)
        await call.answer()
        return

    option = call.data.split(":", 1)[1]

    if question.get("multi"):
        selected = answers.get(question["key"], [])
        if option not in selected:
            selected.append(option)
        answers[question["key"]] = selected
        await state.update_data(answers=answers)

        db = SessionLocal()
        client = db.query(Client).get(client_id)
        setattr(client, question["key"], ", ".join(selected))
        db.commit()
        db.close()

        kb = InlineKeyboardMarkup(row_width=2)
        for opt in question["options"]:
            if opt not in selected:
                kb.insert(InlineKeyboardButton(opt, callback_data=f"option:{opt}"))
        kb.add(InlineKeyboardButton("Далі ➡️", callback_data="next_question"))
        await call.message.edit_text(question["text"], reply_markup=kb)
    else:
        answers[question["key"]] = option
        await state.update_data(answers=answers)

        db = SessionLocal()
        client = db.query(Client).get(client_id)
        setattr(client, question["key"], option)
        db.commit()
        db.close()

        await call.message.edit_text(client_card_text(client))
        await next_question(call.message, state)

    await call.answer()

# Переход к следующему вопросу
async def next_question(message_or_call, state: FSMContext):
    data = await state.get_data()
    question_idx = data["question_idx"] + 1
    client_id = data["client_id"]

    if question_idx >= len(QUESTIONS):
        db = SessionLocal()
        client = db.query(Client).get(client_id)
        db.close()
        await message_or_call.answer(client_card_text(client), reply_markup=client_actions_kb(client_id))
        await state.finish()
        return

    await state.update_data(question_idx=question_idx)
    question = QUESTIONS[question_idx]

    if question.get("multi"):
        kb = InlineKeyboardMarkup(row_width=2)
        selected = data.get("answers", {}).get(question["key"], [])
        for opt in question["options"]:
            if opt not in selected:
                kb.insert(InlineKeyboardButton(opt, callback_data=f"option:{opt}"))
        kb.add(InlineKeyboardButton("Далі ➡️", callback_data="next_question"))
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.message.edit_text(question["text"], reply_markup=kb)
        else:
            await message_or_call.answer(question["text"], reply_markup=kb)
    else:
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.message.edit_text(question["text"])
        else:
            await message_or_call.answer(question["text"])

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_add_client, lambda m: m.text == "➕ Додати клієнта", state="*")
    dp.register_message_handler(handle_text_answer, state=AddClient.waiting_for_answer)
    dp.register_callback_query_handler(handle_option, lambda c: c.data.startswith("option:") or c.data == "next_question", state=AddClient.waiting_for_answer)
