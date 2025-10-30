import re
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Client, ClientPhoto
from backend.services.parse_program_message import (
    parse_and_save_rehab_program,
    parse_and_save_homework_program,
)


def parse_message_client(message_text: str, photo_ids: list[str] = None):
    db: Session = SessionLocal()

    # 1. Ім’я (прибираємо "Реабілітація:")
    first_line = message_text.splitlines()[0].strip()
    client_name = re.sub(r"(?i)ORTHO (KINEZ|SPIN)", "", first_line)

    # 2. Перевіряємо клієнта
    client = db.query(Client).filter(Client.name == client_name).first()
    if not client:
        client = Client(name=client_name, telegram_id=None)
        db.add(client)
        db.commit()
        print(f"✅ Клієнта {client_name} додано")

    # 3. Витягуємо дані
    symptoms_match = re.search(r"Симптопи:\n([\s\S]*?)\nЩо робить:", message_text)
    activities_match = re.search(r"Що робить:\n([\s\S]*?)\nРезультати дослідження:", message_text)
    research_match = re.search(r"Результати дослідження:\n([\s\S]*?)\nРеабілітація:", message_text)
    massage_match = re.search(r"Масаж:(.*?)(?:\n|$)", message_text)

    client.symptoms = symptoms_match.group(1).strip() if symptoms_match else None
    client.activities = activities_match.group(1).strip() if activities_match else None
    client.research_results = research_match.group(1).strip() if research_match else None
    client.massage_recommendations = massage_match.group(1).strip() if massage_match else None

    # 4. Фото
    if photo_ids:
        for pid in photo_ids:
            client_photo = ClientPhoto(client_id=client.id, photo_url=pid)
            db.add(client_photo)

    print(f"✅ Дані клієнта {client.name} оновлено")
    db.commit()

    # 5. Витягуємо програми
    parse_and_save_rehab_program(db, client, message_text)     # курс 2
    parse_and_save_homework_program(db, client, message_text)  # курс 1

    print(f"🏁 Парсинг клієнта завершено")
    from backend.services.client_message import build_client_message
    build_client_message(client.id)
    db.close()

    return client
