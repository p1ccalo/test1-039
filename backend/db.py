from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
import asyncio




load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
session = SessionLocal()

def init_db():
    import models
    print("📦 models імпортовано:", dir(models))  # DEBUG
    Base.metadata.create_all(bind=engine)
    print("✅ Таблиці створені у orthospin.db")
    
async def save_client(data: dict):
    await asyncio.sleep(0)
    return True

if __name__ == "__main__":
    init_db()
