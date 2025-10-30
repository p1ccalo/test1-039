from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Client, ClientPhoto, Exercise, ProgramExercise, Program
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_client_message(client_id: int):
    """
    Формує повідомлення для клієнта у форматі максимально схожому на вхідний.
    Повертає (message_text, photo_url, reply_markup).
    """
    db: Session = SessionLocal()
    client: Client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        db.close()
        return "❌ Клієнта не знайдено", None, None

    # Фото клієнта (останнє додане)
    photo: ClientPhoto = (
        db.query(ClientPhoto)
        .filter(ClientPhoto.client_id == client.id)
        .order_by(ClientPhoto.id.desc())
        .first()
    )
    photo_url = photo.photo_url if photo else None

    # === Формування тексту ===
    message_lines = []
    message_lines.append(f"{client.name}\n")

    if client.symptoms:
        message_lines.append("Симптопи:\n" + client.symptoms + "\n")
    if client.activities:
        message_lines.append("Що робить:\n" + client.activities + "\n")
    if client.research_results:
        message_lines.append("Результати дослідження:\n" + client.research_results + "\n")
    if client.massage_recommendations:
        message_lines.append("Масаж: " + client.massage_recommendations + "\n")

    # --- Програми клієнта ---
    programs = db.query(Program).filter(Program.client_id == client.id).all()
    for program in programs:
        # Сортуємо вправи за block_number та exercise_order
        exercises = (
            db.query(ProgramExercise)
            .filter(ProgramExercise.program_id == program.id)
            .order_by(
                ProgramExercise.block,
                ProgramExercise.order_num
            )
            .all()
        )

        if not exercises:
            continue

        current_block = None
        for ex in exercises:
            if ex.block != current_block:
                current_block = ex.block
                message_lines.append(f"\nБлок {current_block}\n")

            # Формуємо рядок з вагою/повторами/підходами
            details = ""
            if ex.weight or ex.repeats or ex.sets:
                details = f" {ex.weight or ''}/{ex.repeats or ''}/{ex.sets or ''}"
            exercise = db.query(Exercise).filter(Exercise.id == ex.exercise_id).first()
            message_lines.append(
                f"{ex.order_num}. {exercise.name}{details}"
            )

    db.close()

    message_text = "\n".join(message_lines).strip()

    # --- Кнопка ---
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶ Почати заняття", callback_data=f"start_session:{client.id}")]
        ]
    )

    return message_text, photo_url, keyboard
