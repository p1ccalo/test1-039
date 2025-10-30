import os
from aiogram import types, Dispatcher
from aiogram.types import InputFile
from aiogram.dispatcher import FSMContext
from backend.db import SessionLocal
from backend.models import Client, ClientPhoto, Program
from admin_bot.states.add_client import AddClient
from admin_bot.keyboards.keyboards import client_actions_kb, done_kb, clients_keyboard, client_programs_kb, edit_client_kb, back_btn
from admin_bot.states.states import SearchClientStates, EditClientStates
import dotenv
from backend.utils import get_client_photos, save_client_photo
from config import BASE_DIR, CLIENT_PHOTOS_DIR as client_photos_dir

dotenv.load_dotenv()
userbot_username = os.getenv("USERBOT_USERNAME")

print('BASE_DIR:', BASE_DIR)
print('client_photos_dir:', client_photos_dir)
print('files in dir:', os.listdir(client_photos_dir))# ...


# list clients
async def list_clients(message: types.Message, state: FSMContext):
    db = SessionLocal()
    clients = db.query(Client).all()

    if not clients:
        await message.answer("Немає клієнтів")
        db.close()
        return
    
    text = f'Клієнти: {len(clients)}\n\n'
    text += "Виберіть клієнта або введіть ім'я для пошуку:\n\n"
    kb = clients_keyboard(clients)
    await SearchClientStates.query.set()
    
    await message.answer(text, reply_markup=kb)


def client_card_text(client: Client):
    text = f"👤 Ім'я: {client.name}\n"
    text += f"👦 Дата народження: {client.birth_date} ({client.age} роки)\n"
    text += "\nСимптоми:\n"
    text += f"🔎 Що турбує: {client.symptoms}\n"
    text += f"Де турбує: {client.symptoms_where}\n"
    text += f"Як давно турбує: {client.symptoms_how_long}\n"
    text += f"Рівень болю: {client.symptoms_pain_level}\n"
    text += f"Тиск: {client.blood_pressure}\n"
    text += f"🎯 Що робить: {client.activities}\n"
    text += f"\n🔬 Результати дослідження:\n"
    text += f"Стопи: {client.research_feet}\n"
    text += f"Коліна: {client.research_knees}\n"
    text += f"Таз: {client.research_pelvis}\n"
    text += f"Постава: {client.research_posture}\n"
    text += "\n Функціональні тести:\n"
    text += "Спина тригери:\n"
    text += f"- грудний відділ: {client.func_back_thoracic}\n"
    text += f"- поперековий відділ: {client.func_back_lumbar}\n"
    text += f"- шия: {client.func_back_neck}\n"
    text += f"Кульшові суглоби: {client.func_hips}\n"
    text += f"Колінні суглоби: {client.func_knees}\n"
    text += f"Гомілковостопні суглоби: {client.func_ankles}\n"
    text += f"Стопи: {client.func_feet}\n"
    text += f"Симетрія нижніх кінцівок: {client.func_symmetry}\n"
    text += f"Плечі: {client.func_shoulders}\n"
    text += f"Лікті: {client.func_elbows}\n"
    text += f"Зап'ястя: {client.func_wrists}\n"
    text += "\nПобут / Спосіб життя:\n"
    text += f"Умови роботи: {client.work_conditions}\n"
    text += f"Заняття спортом/фітнесом: {client.sport}\n"
    text += f"Використання БАД у харчуванні: {client.supplements}\n"
    text += f"Використання запобіжних масажерів або тренажерів в домашніх умовах: {client.home_devices}\n"
    text += "\nВисновки та рекомендації\n"
    text += "1. Комплексно терапевтичний масаж (кількість/періодичність)\nПроекція масажу:\n"
    text += f"- Класифікація масажу (глибокотканний, нейроседативний, спортивний, лімфодренажний):\n {client.massage_recommendation}"
    text += f"Виготовлення індивідуальних ортопедичних устілок:\n {client.insoles}\n"
    text += f"Запобіжні прилади для профілактики в домашніх умовах:\n {client.preventive_devices}\n"
    text += f"\n🔗 Посилання для активації бота: https://t.me/{userbot_username}?start={client.id}"
    if client.programs:
        text += "\n\n----\n"
        text += f"Програми: ({len(client.programs)})\n"
        for program in client.programs:
            text += f"- {program.course.name}\n"
    return text

from aiogram.types import InputMediaPhoto

async def client_card(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    print('client_id: ', client_id)
    db = SessionLocal()
    client = db.query(Client).get(client_id)

    text = client_card_text(client)
    kb = client_actions_kb(client_id)
    client_photos = db.query(ClientPhoto).filter(ClientPhoto.client_id == client_id).all()
    print('client_photos: ', client_photos)
    media = []
    if client_photos:
        for photo in client_photos:
            print('photo url: ', photo.photo_url)
            photo_path = os.path.join(client_photos_dir, f"{photo.photo_url}.jpg")
            print('photo_path: ', photo_path)
            if os.path.exists(photo_path):
                media.append(types.InputMediaPhoto(media=types.InputFile(photo_path)))
            else:
                print('photo_path does not exist:', photo_path)
    else:
        print('No client photos')
    if media:
        await call.message.answer_media_group(media=media)
        await call.message.answer(text, reply_markup=kb)
    else:
        await call.message.answer(text, reply_markup=kb)
    db.close()
    await EditClientStates.card.set()
    return



async def edit_client_programs(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    programs = client.programs
    text = ""
    if programs:
        text = 'Виберіть програму для редагування:\n\n'
        kb = client_programs_kb(client)
    else:
        text = 'Немає програм'
        kb = None
    db.close()
    await call.message.edit_text(text, reply_markup=kb)


async def edit_client(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    kb = edit_client_kb(client.id)
    text = "✏️ Змінити клієнта\n\n"
    text += client_card_text(client)
    if call.message.caption:
        await call.message.edit_caption(text, reply_markup=kb)
    else:
        await call.message.edit_text(text, reply_markup=kb)
    db.close()
    

async def edit_client_photos(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await call.message.edit_text("Надійшліть фото:")
    await EditClientStates.photos.set()


async def save_client_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    db = SessionLocal()
    client = db.query(Client).get(client_id)

    if not client:
        db.close()
        return None

    # Створюємо директорію, якщо її ще немає
    os.makedirs(client_photos_dir, exist_ok=True)

    # Отримуємо файл від Telegram
    photo = message.photo[-1]
    print('photo: ', photo)
    file = await message.bot.get_file(photo.file_id)
    file_path = os.path.join(client_photos_dir, f"{photo.file_unique_id}.jpg")

    # Завантажуємо файл
    await message.bot.download_file(file.file_path, file_path)
    print('file_path: ', file_path)

    # Зберігаємо шлях у базу
    client_photo = ClientPhoto(client_id=client_id, photo_url=photo.file_unique_id)
    db.add(client_photo)
    db.commit()
    db.close()
    await message.answer("✅ Фото збережено!", reply_markup=back_btn(f"edit_client:{client_id}"))



async def delete_client(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    db.delete(client)
    db.commit()
    db.close()
    await call.message.edit_text("✅ Клієнт видалений!")


async def search_client_query(message: types.Message, state: FSMContext):
    query = message.text.strip()
    db = SessionLocal()
    clients = db.query(Client).filter(Client.name.ilike(f"%{query}%")).all()
    db.close()
    if not clients:
        await message.answer("Нічого не знайдено")
    else:
        await message.answer("🔎 Результати пошуку:", reply_markup=clients_keyboard(clients))
    await state.finish()


async def edit_client_name(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    await state.update_data(name=client.name)
    await call.message.edit_text("Введіть нове ім'я:")
    await EditClientStates.name.set()
    db.close()


async def save_client_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    client.name = message.text.strip()
    db.commit()
    db.close()
    await message.answer("✅ Клієнт оновлений!", reply_markup=back_btn(f"edit_client:{client_id}"))
    await state.finish()


async def edit_client_age(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    await state.update_data(client_id=client_id)
    await call.message.edit_text("Введіть новий вік:")
    await EditClientStates.age.set()
    db.close()


async def save_client_age(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    client.age = int(message.text.strip())
    db.commit()
    db.close()
    await message.answer("✅ Клієнт оновлений!", reply_markup=back_btn(f"edit_client:{client_id}"))
    await state.finish()


async def edit_client_symptoms(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await call.message.edit_text("Введіть нові симптоми:")
    await EditClientStates.symptoms.set()


async def save_client_symptoms(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    client.symptoms = message.text.strip()
    db.commit()
    db.close()
    await message.answer("✅ Клієнт оновлений!", reply_markup=back_btn(f"edit_client:{client_id}"))
    await state.finish()


async def edit_client_research(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await call.message.edit_text("Введіть нові рекомендації:")
    await EditClientStates.research.set()


async def save_client_research(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    client.research = message.text.strip()
    db.commit()
    db.close()
    await message.answer("✅ Клієнт оновлений!", reply_markup=back_btn(f"edit_client:{client_id}"))
    await state.finish()


async def edit_client_massage_recommedations(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await call.message.edit_text("Введіть нові рекомендації:")
    await EditClientStates.massage.set()


async def save_client_massage_recommedations(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    client.massage = message.text.strip()
    db.commit()
    db.close()
    await message.answer("✅ Клієнт оновлений!", reply_markup=back_btn(f"edit_client:{client_id}"))
    await state.finish()


async def edit_client_activities(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await call.message.edit_text("Введіть нові рекомендації:")
    await EditClientStates.activities.set()


async def save_client_activities(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    client.activities = message.text.strip()
    db.commit()
    db.close()
    await message.answer("✅ Клієнт оновлений!", reply_markup=back_btn(f"edit_client:{client_id}"))
    await state.finish()


async def edit_client_photos(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split(":")[1])
    await state.update_data(client_id=client_id)
    if call.message.caption:
        await call.message.edit_caption("Надійшліть нові фото:")
    else:
        await call.message.edit_text("Надійшліть нові фото:")
    await EditClientStates.photos.set()


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(list_clients, lambda m: m.text == '👤 Клієнти', state='*')
    dp.register_message_handler(search_client_query, state=SearchClientStates.query)
    dp.register_callback_query_handler(client_card, lambda c: c.data.startswith("client:"), state='*')
    dp.register_callback_query_handler(edit_client_programs, lambda c: c.data.startswith("edit_programs:"), state='*')
    dp.register_callback_query_handler(delete_client, lambda c: c.data.startswith("delete_client:"), state='*')
    dp.register_callback_query_handler(edit_client, lambda c: c.data.startswith("edit_client:"), state='*')
    
    dp.register_callback_query_handler(edit_client_name, lambda c: c.data.startswith("edit_client_name:"), state='*')
    dp.register_callback_query_handler(edit_client_age, lambda c: c.data.startswith("edit_client_age:"), state='*')
    dp.register_callback_query_handler(edit_client_symptoms, lambda c: c.data.startswith("edit_client_symptoms:"), state='*')
    dp.register_callback_query_handler(edit_client_activities, lambda c: c.data.startswith("edit_client_activities:"), state='*')
    dp.register_callback_query_handler(edit_client_research, lambda c: c.data.startswith("edit_client_research:"), state='*')
    dp.register_callback_query_handler(edit_client_massage_recommedations, lambda c: c.data.startswith("edit_client_massage:"), state='*')
    dp.register_message_handler(save_client_name, state=EditClientStates.name)
    dp.register_message_handler(save_client_age, state=EditClientStates.age)
    dp.register_message_handler(save_client_symptoms, state=EditClientStates.symptoms)
    dp.register_message_handler(save_client_activities, state=EditClientStates.activities)
    dp.register_message_handler(save_client_research, state=EditClientStates.research)
    dp.register_message_handler(save_client_massage_recommedations, state=EditClientStates.massage)
    dp.register_message_handler(save_client_photo, content_types=['photo', 'text'], state=EditClientStates.photos)
    dp.register_callback_query_handler(edit_client_photos, lambda c: c.data.startswith("edit_client_photos:"), state='*')
