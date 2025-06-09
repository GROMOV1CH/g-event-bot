from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_, or_
from models import Event, User, Poll, Vote, Base
from datetime import datetime, timedelta, timezone
from config import settings
from typing import List, Optional
import json
import python_jwt as jwt
import os
import hashlib
import hmac
import urllib.parse

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./events.db")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

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

# Зависимость для получения сессии БД
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# Зависимость для проверки JWT токена
def verify_token(request: Request) -> dict:
    token = request.headers.get('Authorization')
    if not token:
        raise HTTPException(status_code=401, detail="Token not found")
    
    try:
        payload = jwt.decode(token.split()[1], os.getenv("JWT_SECRET"), algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Зависимость для проверки прав администратора
def verify_admin(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.telegram_id == token_data['user_id']).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

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

@app.get("/api/events")
async def get_events(
    type: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    now = datetime.now(timezone.utc)
    query = db.query(Event)
    
    if type == "upcoming":
        query = query.filter(Event.date >= now)
    elif type == "past":
        query = query.filter(Event.date < now)
    else:
        raise HTTPException(status_code=400, detail="Invalid event type")
    
    events = query.order_by(Event.date).all()
    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date.isoformat(),
            "location": event.location
        }
        for event in events
    ]

@app.get("/api/events/all")
async def get_all_events(
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    events = db.query(Event).order_by(Event.date).all()
    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date.isoformat(),
            "location": event.location
        }
        for event in events
    ]

@app.get("/api/events/{event_id}")
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date.isoformat(),
        "location": event.location
    }

@app.post("/api/events")
async def create_event_in_db(
    event: dict,
    db: Session = Depends(get_db),
    user: User = Depends(verify_admin)
):
    new_event = Event(
        title=event['title'],
        description=event['description'],
        date=datetime.fromisoformat(event['date']),
        location=event['location'],
        created_by=user.id
    )
    db.add(new_event)
    db.commit()
    return {"message": "Event created successfully"}

@app.put("/api/events/{event_id}")
async def update_event(
    event_id: int,
    event: dict,
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db_event.title = event['title']
    db_event.description = event['description']
    db_event.date = datetime.fromisoformat(event['date'])
    db_event.location = event['location']
    
    db.commit()
    return {"message": "Event updated successfully"}

@app.delete("/api/events/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    return {"message": "Event deleted successfully"}

@app.get("/api/polls")
async def get_polls(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    now = datetime.now(timezone.utc)
    user = db.query(User).filter(User.telegram_id == token_data['user_id']).first()
    
    polls = db.query(Poll).filter(Poll.end_date >= now).order_by(Poll.end_date).all()
    
    # Проверяем, голосовал ли пользователь в каждом опросе
    result = []
    for poll in polls:
        voted = db.query(Vote).filter(
            and_(Vote.poll_id == poll.id, Vote.user_id == user.id)
        ).first() is not None
        
        poll_data = {
            "id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "endDate": poll.end_date.isoformat(),
            "options": poll.options,
            "voted": voted
        }
        
        if voted:
            # Если пользователь уже проголосовал, показываем результаты
            poll_data["results"] = [
                {
                    "text": option["text"],
                    "votes": option["votes"]
                }
                for option in poll.options
            ]
        
        result.append(poll_data)
    
    return result

@app.get("/api/polls/all")
async def get_all_polls(
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    polls = db.query(Poll).order_by(Poll.end_date).all()
    return [
        {
            "id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "endDate": poll.end_date.isoformat(),
            "options": poll.options
        }
        for poll in polls
    ]

@app.get("/api/polls/{poll_id}")
async def get_poll(
    poll_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    return {
        "id": poll.id,
        "title": poll.title,
        "description": poll.description,
        "endDate": poll.end_date.isoformat(),
        "options": poll.options
    }

@app.post("/api/polls")
async def create_poll(
    poll: dict,
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    new_poll = Poll(
        title=poll['title'],
        description=poll['description'],
        end_date=datetime.fromisoformat(poll['endDate']),
        options=[{"text": opt["text"], "votes": 0} for opt in poll['options']]
    )
    db.add(new_poll)
    db.commit()
    return {"message": "Poll created successfully"}

@app.put("/api/polls/{poll_id}")
async def update_poll(
    poll_id: int,
    poll: dict,
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    db_poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not db_poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    # Сохраняем текущие голоса
    current_votes = {opt["text"]: opt["votes"] for opt in db_poll.options}
    
    # Обновляем опрос, сохраняя голоса для существующих опций
    db_poll.title = poll['title']
    db_poll.description = poll['description']
    db_poll.end_date = datetime.fromisoformat(poll['endDate'])
    db_poll.options = [
        {
            "text": opt["text"],
            "votes": current_votes.get(opt["text"], 0)
        }
        for opt in poll['options']
    ]
    
    db.commit()
    return {"message": "Poll updated successfully"}

@app.delete("/api/polls/{poll_id}")
async def delete_poll(
    poll_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_admin)
):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    # Удаляем все голоса для этого опроса
    db.query(Vote).filter(Vote.poll_id == poll_id).delete()
    db.delete(poll)
    db.commit()
    return {"message": "Poll deleted successfully"}

@app.post("/api/polls/{poll_id}/vote")
async def vote_in_poll(
    poll_id: int,
    vote: dict,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    user = db.query(User).filter(User.telegram_id == token_data['user_id']).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверяем, существует ли опрос и не закончился ли он
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    if poll.end_date < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Poll has ended")
    
    # Проверяем, не голосовал ли пользователь уже
    existing_vote = db.query(Vote).filter(
        and_(Vote.poll_id == poll_id, Vote.user_id == user.id)
    ).first()
    
    if existing_vote:
        raise HTTPException(status_code=400, detail="User has already voted")
    
    # Проверяем корректность индекса опции
    option_index = vote['optionIndex']
    if option_index < 0 or option_index >= len(poll.options):
        raise HTTPException(status_code=400, detail="Invalid option index")
    
    # Создаем запись о голосе
    new_vote = Vote(
        poll_id=poll_id,
        user_id=user.id,
        option_index=option_index
    )
    db.add(new_vote)
    
    # Увеличиваем счетчик голосов для выбранной опции
    poll.options[option_index]['votes'] += 1
    
    db.commit()
    return {"message": "Vote recorded successfully"}

def verify_telegram_data(init_data: str) -> dict:
    """Проверяет подлинность данных от Telegram Web App."""
    try:
        # Разбираем строку init_data
        parsed_data = dict(urllib.parse.parse_qsl(init_data))
        
        # Получаем и удаляем hash из данных
        received_hash = parsed_data.pop('hash')
        
        # Сортируем оставшиеся поля
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])
        
        # Создаем секретный ключ
        secret_key = hmac.new(
            "WebAppData".encode(),
            os.getenv("BOT_TOKEN").encode(),
            hashlib.sha256
        ).digest()
        
        # Вычисляем хеш
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем хеши
        if calculated_hash != received_hash:
            raise ValueError("Invalid hash")
        
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

@app.post("/api/verify_admin")
async def verify_admin(request: Request):
    """Проверяет права администратора для Telegram Web App."""
    try:
        data = await request.json()
        user_data = data.get('user', {})
        user_id = user_data.get('id')
        
        if not user_id:
            return {"is_admin": False, "error": "No user ID provided"}
        
        # Список ID администраторов (замените на ваш ID)
        admin_ids = [1234567890]  # Замените на ваш ID из Telegram
        
        return {
            "is_admin": user_id in admin_ids,
            "user_id": user_id
        }
    except Exception as e:
        return {"is_admin": False, "error": str(e)} 