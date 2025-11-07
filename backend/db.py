import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from typing import AsyncGenerator

# Завантажуємо .env (щоб отримати DATABASE_URL)
load_dotenv()





if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL не знайдено в .env")

# Створюємо engine
engine = create_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Створюємо сесію
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для моделей
Base = declarative_base()

# Ініціалізація БД
def init_db():
    import backend.models  # або просто import models, якщо в тій самій папці
    print("📦 Імпортовано моделі:", dir(backend.models))
    Base.metadata.create_all(bind=engine)
    print("✅ Таблиці синхронізовано з PostgreSQL")
    
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# Для локального запуску
if __name__ == "__main__":
    init_db()
