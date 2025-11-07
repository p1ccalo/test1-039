from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

DATABASE_URL= os.getenv("DATABASE_URL") or "sqlite:///./backend/database.db"
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
BASE_DIR = Path(__file__).resolve().parent
CLIENT_PHOTOS_DIR = BASE_DIR / "static" / "images" / "client_photos"
EXERCISE_PHOTOS_DIR = BASE_DIR / "static" / "images" / "exercise_photos"
CLIENT_PHOTOS_DIR = os.getenv("CLIENT_PHOTOS_DIR", BASE_DIR / "static" / "images" / "client_photos")