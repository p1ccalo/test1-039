
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🏋️‍♂️ Почати заняття')],
        [KeyboardButton(text='👤 Мій профіль'), KeyboardButton(text='📋 Мої програми')],
        [KeyboardButton(text='✨ Корисне приладдя'), KeyboardButton(text='💼 Послуги')],
        [KeyboardButton(text='ℹ️ Корисне'), KeyboardButton(text='🏥 Про Orthospin')],
        [KeyboardButton(text='⚙️ Налаштування'), KeyboardButton(text='❓ Допомога')],
    ],
    resize_keyboard=True
)

def back_kb(callback_data: str):
    return InlineKeyboardButton('Назад', callback_data=callback_data)