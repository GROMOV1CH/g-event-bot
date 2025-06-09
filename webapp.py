from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_, or_, func
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
    type: str = "upcoming",
    category: Optional[str] = None,
    month: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получает список мероприятий с фильтрацией."""
    now = datetime.now(timezone.utc)
    query = db.query(Event)

    # Фильтр по типу (предстоящие/прошедшие)
    if type == "upcoming":
        query = query.filter(Event.date >= now)
    else:
        query = query.filter(Event.date < now)

    # Фильтр по категории
    if category:
        query = query.filter(Event.category == category)

    # Фильтр по месяцу
    if month is not None:
        query = query.filter(func.extract('month', Event.date) == month)

    # Поиск по тексту
    if search:
        search_filter = or_(
            Event.title.ilike(f"%{search}%"),
            Event.description.ilike(f"%{search}%"),
            Event.location.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Сортировка
    if type == "upcoming":
        query = query.order_by(Event.date.asc())
    else:
        query = query.order_by(Event.date.desc())

    events = query.all()
    return events

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
async def create_event(request: Request, db: Session = Depends(get_db)):
    """Создает новое мероприятие."""
    try:
        data = await request.json()
        
        # Проверяем обязательные поля
        if not all(key in data for key in ['title', 'description', 'date']):
            raise HTTPException(status_code=400, detail="Не все обязательные поля заполнены")
        
        # Создаем мероприятие
        event = Event(
            title=data["title"],
            description=data["description"],
            date=datetime.fromisoformat(data["date"].replace('Z', '+00:00')),
            location=data.get("location"),
            category=data.get("category", "other")
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        # Возвращаем созданное мероприятие
        return {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date.isoformat(),
            "location": event.location,
            "category": event.category
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Неверный формат данных: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания мероприятия: {str(e)}")

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
async def get_polls(db: Session = Depends(get_db)):
    """Получает список активных опросов."""
    now = datetime.now(timezone.utc)
    polls = db.query(Poll).filter(Poll.end_date >= now).all()
    
    # Подсчитываем голоса для каждого варианта
    for poll in polls:
        total_votes = sum(len(option.votes) for option in poll.options)
        for option in poll.options:
            option_votes = len(option.votes)
            option.votes_count = option_votes
            option.votes_percentage = (option_votes / total_votes * 100) if total_votes > 0 else 0
    
    return polls

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
async def create_poll(request: Request, db: Session = Depends(get_db)):
    """Создает новый опрос."""
    try:
        data = await request.json()
        
        # Проверяем обязательные поля
        if not all(key in data for key in ['title', 'description', 'endDate', 'options']):
            raise HTTPException(status_code=400, detail="Не все обязательные поля заполнены")
        
        if len(data['options']) < 2:
            raise HTTPException(status_code=400, detail="Опрос должен содержать минимум 2 варианта ответа")
        
        # Создаем опрос
        poll = Poll(
            title=data["title"],
            description=data["description"],
            end_date=datetime.fromisoformat(data["endDate"].replace('Z', '+00:00'))
        )
        
        db.add(poll)
        db.flush()  # Получаем ID опроса
        
        # Создаем варианты ответов
        for option_data in data["options"]:
            option = PollOption(
                poll_id=poll.id,
                text=option_data["text"]
            )
            db.add(option)
        
        db.commit()
        db.refresh(poll)
        
        # Возвращаем созданный опрос
        return {
            "id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "end_date": poll.end_date.isoformat(),
            "options": [{"id": opt.id, "text": opt.text} for opt in poll.options]
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Неверный формат данных: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания опроса: {str(e)}")

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
        
        # Список ID администраторов
        admin_ids = [677621800]  # Ваш Telegram ID
        
        print(f"Checking admin rights for user {user_id}. Is admin: {user_id in admin_ids}")
        
        return {
            "is_admin": user_id in admin_ids,
            "user_id": user_id
        }
    except Exception as e:
        print(f"Error in verify_admin: {str(e)}")
        return {"is_admin": False, "error": str(e)}

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Получает статистику для админ-панели."""
    now = datetime.now(timezone.utc)
    
    # Статистика мероприятий
    total_events = db.query(func.count(Event.id)).scalar()
    upcoming_events = db.query(func.count(Event.id)).filter(Event.date >= now).scalar()
    past_events = db.query(func.count(Event.id)).filter(Event.date < now).scalar()
    
    # Статистика опросов
    total_polls = db.query(func.count(Poll.id)).scalar()
    active_polls = db.query(func.count(Poll.id)).filter(Poll.end_date >= now).scalar()
    completed_polls = db.query(func.count(Poll.id)).filter(Poll.end_date < now).scalar()
    
    # Статистика пользователей
    total_users = db.query(func.count(User.id)).scalar()
    active_today = db.query(func.count(User.id)).filter(
        User.last_active >= now - timedelta(days=1)
    ).scalar()
    new_this_week = db.query(func.count(User.id)).filter(
        User.created_at >= now - timedelta(days=7)
    ).scalar()
    
    return {
        "events": {
            "total": total_events,
            "upcoming": upcoming_events,
            "past": past_events,
            "by_category": db.query(
                Event.category,
                func.count(Event.id)
            ).group_by(Event.category).all()
        },
        "polls": {
            "total": total_polls,
            "active": active_polls,
            "completed": completed_polls,
            "total_votes": db.query(func.count(Vote.id)).scalar()
        },
        "users": {
            "total": total_users,
            "active_today": active_today,
            "new_this_week": new_this_week
        }
    } 