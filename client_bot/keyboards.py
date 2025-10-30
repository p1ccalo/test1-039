
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton('🏋️‍♂️ Почати заняття')],
        [KeyboardButton('👤 Мій профіль'), KeyboardButton('📋 Мої програми')],
        [KeyboardButton('✨ Корисне приладдя'), KeyboardButton('💼 Послуги')],
        [KeyboardButton('ℹ️ Корисне'), KeyboardButton('🏥 Про Orthospin')],
        [KeyboardButton('⚙️ Налаштування'), KeyboardButton('❓ Допомога')],
    ],
    resize_keyboard=True
)

def back_kb(callback_data: str):
    return InlineKeyboardButton('Назад', callback_data=callback_data)