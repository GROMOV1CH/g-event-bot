from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import Event, User
from datetime import datetime
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
        # TODO: добавить проверку данных от Telegram Web App
        return data
    except:
        return {}

@app.get("/webapp")
async def webapp(request: Request):
    """Главная страница веб-приложения"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/api/events/upcoming")
async def get_upcoming_events():
    """Получить предстоящие мероприятия"""
    # TODO: добавить работу с БД
    return {"events": []}

@app.get("/api/events/past")
async def get_past_events():
    """Получить прошедшие мероприятия"""
    # TODO: добавить работу с БД
    return {"events": []}

@app.get("/api/admin/events")
async def admin_events(request: Request):
    """Админ-панель для управления мероприятиями"""
    # TODO: добавить проверку на админа
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )

@app.get("/")
async def root():
    return {"status": "ok", "message": "Event Management Bot API"} 