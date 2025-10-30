
import requests
import os
from dotenv import load_dotenv
from backend.db import session, SessionLocal
from backend.models import Client, Program, ClientPhoto, Exercise, ExercisePhoto
import re
from sqlalchemy.orm import Session
from aiogram import types

load_dotenv()

BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')
client_photos_dir = os.getenv("CLIENT_PHOTOS_DIR")

def get_client_by_tg(tg_id: str):
    client = session.query(Client).filter_by(telegram_id=tg_id).first()
    return client

def get_client_exercises(client_id: int):
    programs = session.query(Program).filter_by(client_id=client_id).all()
    return [p.exercises for p in programs]

def get_client_program_exercises(client_id: int, program_id: int):
    program = session.query(Program).filter_by(client_id=client_id, id=program_id).first()
    return program.exercises


def set_client_happies(client_id: int, happies: int):
    client = session.query(Client).filter_by(id=client_id).first()
    client.happies = client.happies + happies
    session.commit()



def get_products(category: str = None):
    params = {'category': category} if category else {}
    r = requests.get(f"{BACKEND_URL}/api/products", params=params)
    if r.status_code == 200:
        return r.json().get('products', [])
    return []

def get_services():
    r = requests.get(f"{BACKEND_URL}/api/services")
    if r.status_code == 200:
        return r.json().get('services', [])
    return []

def get_articles():
    r = requests.get(f"{BACKEND_URL}/api/articles")
    if r.status_code == 200:
        return r.json().get('articles', [])
    return []


def get_or_create_program(db: Session, client_id: int, course_id: int):
    """
    Перевіряє, чи вже є у клієнта програма для курсу.
    Якщо є → повертає її, якщо ні → створює нову.
    """
    program = db.query(Program).filter(
        Program.client_id == client_id,
        Program.course_id == course_id
    ).first()

    if program:
        print(f"⚠️ Програма курсу {course_id} вже існує")
        return program, False

    program = Program(client_id=client_id, course_id=course_id)
    db.add(program)
    db.commit()
    print(f"✅ Створено нову програму для курсу {course_id}")
    return program, True

async def save_client_photo(client_id: int, message: types.Message):
    db = SessionLocal()
    client = db.query(Client).get(client_id)

    if not client:
        db.close()
        return None

    # Створюємо директорію, якщо її ще немає
    client_dir = os.path.join(client_photos_dir, str(client_id))
    os.makedirs(client_dir, exist_ok=True)

    # Отримуємо файл від Telegram
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = os.path.join(client_dir, f"{photo.file_unique_id}.jpg")

    # Завантажуємо файл
    await message.bot.download_file(file.file_path, file_path)

    # Зберігаємо шлях у базу
    client_photo = ClientPhoto(client_id=client_id, photo_url=photo.file_unique_id)
    db.add(client_photo)
    db.commit()
    db.close()

    return file_path


def get_client_photos(client_id: int):
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    db.close()
    photos = [photo.photo_url for photo in client.photos]
    return photos


async def save_exercise_photos(exercise_id: int, message: types.Message):
    db = SessionLocal()

    # Створюємо директорію, якщо її ще немає
    exercise_dir = os.getenv('EXERCISE_PHOTOS_DIR')
    os.makedirs(exercise_dir, exist_ok=True)

    # Отримуємо файл від Telegram
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = os.path.join(exercise_dir, f"{photo.file_unique_id}.jpg")

    # Завантажуємо файл
    await message.bot.download_file(file.file_path, file_path)

    photo = ExercisePhoto(exercise_id=exercise_id, photo_url=photo.file_unique_id)

    db.commit()
    db.close()

    return file_path
    

# def parse_message_client(message_text: str, photo_id: str = None):
#     db: Session = SessionLocal()

#     # 1. Ім’я
#     first_line = message_text.splitlines()[0].strip()

#     # Прибираємо можливе "Реабілітація:"
#     client_name = first_line.replace("Реабілітація:", "").replace("ORTHO KINEZ", "").replace("ORTHO SPIN").strip()

#     # 2. Перевіряємо клієнта
#     client = db.query(Client).filter(Client.name == client_name).first()
#     if not client:
#         client = Client(
#             name=client_name, 
#             telegram_id=None)
#         db.add(client)
#         print("✅ Клієнта додано")
#         db.commit()

#     # 3. Витягуємо дані
#     symptoms_match = re.search(r"Симптопи:\n([\s\S]*?)\nЩо робить:", message_text)
#     activities_match = re.search(r"Що робить:\n([\s\S]*?)\nРезультати дослідження:", message_text)
#     print('activities_match', activities_match)
#     research_match = re.search(r"Результати дослідження:\n([\s\S]*?)\nРеабілітація:", message_text)
#     massage_match = re.search(r"Масаж:(.*?)(?:\n|$)", message_text)

#     client.symptoms = symptoms_match.group(1).strip() if symptoms_match else None
#     client.activities = activities_match.group(1).strip() if activities_match else None
#     # client.research_results = research_match.group(1).strip() if research_match else None
    # client.massage_recommendations = massage_match.group(1).strip() if massage_match else None
    # db.commit()

    # # 4. Фото
    # if photo_id:
    #     client_photo = ClientPhoto(client_id=client.id, photo_url=photo_id)
    #     db.add(client_photo)

    # print('✅ Дані клієнта оновлено')
    # db.commit()

    # # Витягуємо вправи кінезіотерапії
    # from backend.services.parse_program_message import parse_and_save_rehab_program
    # parse_and_save_rehab_program(db, client, message_text)
    # print("✅ Програма додана")
    # db.commit()
    # db.close()


