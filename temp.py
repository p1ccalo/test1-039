from backend.db import engine
from sqlalchemy import text

tables = [
    "users",
    "admins",
    "courses",
    "programs",
    "exercises",
    "clients",
    "client_photos",
    "exercise_photos",
    "program_exercise"
]

with engine.connect() as conn:
    for table in tables:
        seq_name = f"{table}_id_seq"
        print(f"⚙️ Налаштовую {table} ...")

        # створюємо sequence, якщо немає
        conn.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name};"))

        # прив’язуємо id до sequence
        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT nextval('{seq_name}');"))

        # отримуємо максимальний id у таблиці
        result = conn.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table};"))
        max_id = result.scalar() or 0

        # виставляємо sequence на наступне значення після максимального id
        conn.execute(text(f"ALTER SEQUENCE {seq_name} RESTART WITH {max_id + 1};"))

    conn.commit()

print("✅ Усі sequence синхронізовано з існуючими ID!")