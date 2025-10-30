from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from backend.models import Client, Program
from backend.db import SessionLocal

main_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
main_menu.add(KeyboardButton('➕ Додати клієнта'))
main_menu.add(KeyboardButton('👤 Клієнти'))
main_menu.add(KeyboardButton('🏷 Вправи'))
main_menu.add(KeyboardButton('📁 Шаблони'))


# inline helpers
def client_actions_kb(client_id: int):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton('📋 Програми', callback_data=f'edit_programs:{client_id}'))
    kb.add(InlineKeyboardButton('✏️ Редагувати', callback_data=f'edit_client:{client_id}'))
    kb.add(InlineKeyboardButton('❌ Видалити', callback_data=f'delete_client:{client_id}'))
    kb.add(InlineKeyboardButton('➕ Додати програму', callback_data=f'add_program:{client_id}'))
    return kb

def client_programs_kb(client: Client):
    kb = InlineKeyboardMarkup(row_width=1)
    if client.programs:
        for program in client.programs:
            kb.insert(InlineKeyboardButton(program.course.name, callback_data=f'edit_program:{program.id}'))
    else:
        kb.insert(InlineKeyboardButton('➕ Додати програму', callback_data=f'add_program_for:{client.id}'))
    kb.add(InlineKeyboardButton('Назад', callback_data=f'client:{client.id}'))
    return kb


def program_item_kb(program_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('✏️ Редагувати програму', callback_data=f'edit_program:{program_id}'))
    kb.add(InlineKeyboardButton('🗑 Видалити програму', callback_data=f'delete_program:{program_id}'))
    return kb

# Кнопка "Готово" для фото
done_kb = InlineKeyboardMarkup(row_width=1)
done_kb.add(InlineKeyboardButton("✅ Готово", callback_data="done"))

def clients_keyboard(clients):
    kb = InlineKeyboardMarkup(row_width=2)
    for cl in clients:
        if cl.name:
            kb.insert(InlineKeyboardButton(text=cl.name, callback_data=f"client:{cl.id}"))
        else:
            print(f'client {cl.id} has no name')
    print('kb: ', kb)
    return kb

# Кнопки для редагування вправ
def exercise_edit_kb(ex_id):
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✏️ Змінити назву", callback_data=f"exercise_edit_name:{ex_id}"),
        InlineKeyboardButton("✏️ Змінити опис", callback_data=f"exercise_edit_description:{ex_id}"),
        InlineKeyboardButton("Змінити фото", callback_data=f"exercise_edit_photo:{ex_id}"),
        InlineKeyboardButton("❌ Видалити", callback_data=f"delete_exercise:{ex_id}")
    )
    return kb


def build_program_edit_kb(exercises, program_id, client_id):
    kb = InlineKeyboardMarkup(row_width=4)
    for i, ex in enumerate(exercises):
        row = [
            InlineKeyboardButton(ex.name, callback_data=f"noop:{program_id}_{ex.id}"),
            InlineKeyboardButton("⬆️", callback_data=f"move_up:{program_id}_{ex.id}"),
            InlineKeyboardButton("⬇️", callback_data=f"move_down:{program_id}_{ex.id}"),
            InlineKeyboardButton("✖️", callback_data=f"delete_ex:{program_id}_{ex.id}"),
        ]
        kb.row(*row)
    kb.add(InlineKeyboardButton("➕ Додати вправу", callback_data=f"add_ex:"))
    kb.add(InlineKeyboardButton("✅ Готово", callback_data=f"client:{client_id}")), 
    kb.add(InlineKeyboardButton("❌ Видалити програму", callback_data=f"delete_program:{program_id}"))
    return kb

def back_btn(callback_data):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Назад", callback_data=callback_data))
    return kb


def edit_client_kb(client_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("Змінити ім'я", callback_data=f"edit_client_name:{client_id}"))
    kb.add(InlineKeyboardButton("Змінити вік", callback_data=f"edit_client_age:{client_id}"))
    kb.add(InlineKeyboardButton("Симптоми", callback_data=f"edit_client_symptoms:{client_id}"))
    kb.add(InlineKeyboardButton("Що робить", callback_data=f"edit_client_activities:{client_id}"))
    kb.add(InlineKeyboardButton("Рекомендації з масажу", callback_data=f"edit_client_massage_recommendations:{client_id}"))
    kb.add(InlineKeyboardButton("Додати фото", callback_data=f"edit_client_photos:{client_id}"))
    kb.add(InlineKeyboardButton("Готово", callback_data=f"client:{client_id}"))

    return kb
