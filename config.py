from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

class Settings(BaseModel):
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./events.db")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "http://localhost:8000/webapp")
    ADMIN_USER_IDS: List[int] = [int(id.strip()) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]

    class Config:
        env_file = ".env"

    # Если используется SQLite, убираем параметры подключения PostgreSQL
    if DATABASE_URL.startswith("sqlite"):
        DATABASE_URL = DATABASE_URL
    else:
        # Для PostgreSQL добавляем параметры
        DATABASE_URL = DATABASE_URL + "?sslmode=require"

settings = Settings() 