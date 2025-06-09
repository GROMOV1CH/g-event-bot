from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import Event, User
from datetime import datetime, timedelta
from config import settings
from typing import List
import json

app = FastAPI()

# Подключаем шаблоны и статические файлы
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Функция для проверки инициатора Telegram Web App
async def verify_webapp_data(request: Request):
    try:
        data = await request.json()
        user_id = data.get('user', {}).get('id')
        if user_id:
            return user_id in settings.ADMIN_USER_IDS
        return False
    except:
        return False

@app.get("/webapp")
async def webapp(request: Request):
    """Главная страница веб-приложения"""
    is_admin = False
    try:
        is_admin = await verify_webapp_data(request)
    except:
        pass
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "is_admin": is_admin}
    )

@app.get("/admin")
async def admin_panel(request: Request):
    """Админ-панель"""
    is_admin = await verify_webapp_data(request)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )

@app.get("/api/events/upcoming")
async def get_upcoming_events():
    """Получить предстоящие мероприятия"""
    current_time = datetime.now()
    # TODO: добавить работу с БД
    # Пока возвращаем тестовые данные
    return {"events": [
        {
            "id": 1,
            "title": "Встреча сообщества Python",
            "description": "Ежемесячная встреча разработчиков Python",
            "date": (current_time + timedelta(days=7)).isoformat(),
            "location": "Технопарк"
        },
        {
            "id": 2,
            "title": "Мастер-класс по FastAPI",
            "description": "Изучаем создание современных веб-приложений",
            "date": (current_time + timedelta(days=14)).isoformat(),
            "location": "Онлайн"
        }
    ]}

@app.get("/api/events/past")
async def get_past_events():
    """Получить прошедшие мероприятия"""
    current_time = datetime.now()
    # TODO: добавить работу с БД
    # Пока возвращаем тестовые данные
    return {"events": [
        {
            "id": 3,
            "title": "Хакатон по AI",
            "description": "Разработка AI-проектов за 48 часов",
            "date": (current_time - timedelta(days=7)).isoformat(),
            "location": "IT-центр"
        }
    ]}

@app.post("/api/admin/events")
async def create_event(request: Request):
    """Создание нового мероприятия"""
    is_admin = await verify_webapp_data(request)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    data = await request.json()
    # TODO: добавить сохранение в БД
    return {"status": "success", "message": "Мероприятие создано"}

@app.get("/")
async def root():
    return {"status": "ok", "message": "Event Management Bot API"} 