from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def skip_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустити")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def next_step_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Далі")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def confirm_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="confirm_no")]
    ])
    return kb

def exercises_kb(results):
    kb = InlineKeyboardMarkup()
    for ex in results:
        kb.add(InlineKeyboardButton(text=ex.name, callback_data=f"add_ex:{ex.id}"))
    kb.add(InlineKeyboardButton(text="✅ Завершити формування", callback_data="done_ex"))
    return kb

def courses_kb(courses):
    kb = InlineKeyboardMarkup()
    for c in courses:
        kb.add(InlineKeyboardButton(text=c.title, callback_data=f"course:{c.id}"))
    return kb
