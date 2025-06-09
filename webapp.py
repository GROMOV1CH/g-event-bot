from datetime import datetime, timezone
from typing import List, Optional
import json
import hmac
import urllib.parse
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
import python_jwt as jwt
import os
import hashlib
import os

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Модели Pydantic для валидации данных
class OptionCreate(BaseModel):
    text: str

class PollCreate(BaseModel):
    title: str
    description: str
    end_date: datetime
    options: List[OptionCreate]
    created_by: Optional[int] = None

class EventCreate(BaseModel):
    title: str
    description: str
    date: datetime
    location: Optional[str] = None
    category: str = Field(default="other")
    created_by: Optional[int] = None

# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Определение моделей базы данных
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    last_active = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    is_admin = Column(Boolean, default=False)
    saved_events = relationship("SavedEvent", back_populates="user")
    votes = relationship("Vote", back_populates="user")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    date = Column(DateTime(timezone=True))
    location = Column(String)
    category = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey("users.telegram_id"))
    saved_by = relationship("SavedEvent", back_populates="event")

class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey("users.telegram_id"))
    options = relationship("PollOption", back_populates="poll")

class PollOption(Base):
    __tablename__ = "poll_options"
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    text = Column(String)
    poll = relationship("Poll", back_populates="options")
    votes = relationship("Vote", back_populates="option")

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"))
    option_id = Column(Integer, ForeignKey("poll_options.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    user = relationship("User", back_populates="votes")
    option = relationship("PollOption", back_populates="votes")

class SavedEvent(Base):
    __tablename__ = "saved_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    user = relationship("User", back_populates="saved_events")
    event = relationship("Event", back_populates="saved_by")

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализация FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Создает новое мероприятие."""
    try:
        new_event = Event(
            title=event.title,
            description=event.description,
            date=event.date,
            location=event.location,
            category=event.category,
            created_by=event.created_by
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        
        # Возвращаем созданное мероприятие
        return {
            "id": new_event.id,
            "title": new_event.title,
            "description": new_event.description,
            "date": new_event.date.isoformat(),
            "location": new_event.location,
            "category": new_event.category,
            "created_by": new_event.created_by
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

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
async def create_poll(poll: PollCreate, db: Session = Depends(get_db)):
    """Создает новый опрос."""
    try:
        new_poll = Poll(
            title=poll.title,
            description=poll.description,
            end_date=poll.end_date,
            created_by=poll.created_by
        )
        
        # Добавляем варианты ответов
        for option in poll.options:
            poll_option = PollOption(text=option.text)
            new_poll.options.append(poll_option)
        
        db.add(new_poll)
        db.commit()
        db.refresh(new_poll)
        
        # Возвращаем созданный опрос
        return {
            "id": new_poll.id,
            "title": new_poll.title,
            "description": new_poll.description,
            "end_date": new_poll.end_date.isoformat(),
            "created_by": new_poll.created_by,
            "options": [{"id": opt.id, "text": opt.text} for opt in new_poll.options]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

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

def parse_init_data(init_data: str) -> dict:
    """Парсит init data из Telegram Web App."""
    try:
        # Декодируем URL-encoded строку
        decoded = urllib.parse.unquote(init_data)
        # Разбиваем на параметры
        params = dict(urllib.parse.parse_qsl(decoded))
        # Если есть user в виде строки, преобразуем в словарь
        if 'user' in params and isinstance(params['user'], str):
            params['user'] = json.loads(params['user'])
        return params
    except Exception as e:
        logger.error(f"Error parsing init data: {e}")
        return {}

def verify_telegram_data(init_data: str) -> bool:
    """Проверяет подпись данных от Telegram."""
    try:
        # Получаем параметры
        params = dict(urllib.parse.parse_qsl(init_data))
        
        # Получаем хэш
        hash_value = params.pop('hash', None)
        if not hash_value:
            return False
            
        # Сортируем оставшиеся параметры
        data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(params.items()))
        
        # Создаем HMAC с использованием токена бота
        secret_key = hmac.new(
            key=os.getenv('BOT_TOKEN', '').encode(),
            msg='WebAppData'.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Проверяем подпись
        signature = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return signature == hash_value
    except Exception as e:
        logger.error(f"Error verifying Telegram data: {e}")
        return False

@app.post("/api/auth/init")
async def init_user(request: Request, db: Session = Depends(get_db)):
    """Инициализирует пользователя при первом входе в приложение."""
    try:
        # Получаем init_data из разных возможных источников
        init_data = request.query_params.get("initData")
        if not init_data:
            init_data = request.headers.get("X-Telegram-Init-Data")
            
        if not init_data:
            raise HTTPException(status_code=400, detail="No init data provided")
        
        # Проверяем подпись данных
        if not verify_telegram_data(init_data):
            raise HTTPException(status_code=400, detail="Invalid init data signature")
            
        # Парсим данные пользователя
        user_data = parse_init_data(init_data)
        if not user_data or "user" not in user_data:
            raise HTTPException(status_code=400, detail="Invalid init data format")
            
        tg_user = user_data["user"]
        user = db.query(User).filter(User.telegram_id == tg_user["id"]).first()
        
        if not user:
            # Создаем нового пользователя
            user = User(
                telegram_id=tg_user["id"],
                username=tg_user.get("username"),
                created_at=datetime.now(timezone.utc),
                last_active=datetime.now(timezone.utc)
            )
            db.add(user)
            logger.info(f"Created new user: {tg_user['id']}")
        else:
            # Обновляем время последней активности
            user.last_active = datetime.now(timezone.utc)
            logger.info(f"Updated user activity: {tg_user['id']}")
            
        db.commit()
        return {"success": True, "user_id": tg_user["id"]}
        
    except Exception as e:
        logger.error(f"Error initializing user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/api/admin/users")
async def get_users_stats(db: Session = Depends(get_db)):
    """Получает статистику пользователей для админ-панели."""
    try:
        now = datetime.now(timezone.utc)
        logger.info("Fetching users list")
        
        # Получаем всех пользователей
        users = db.query(User).order_by(User.last_active.desc()).all()
        logger.info(f"Found {len(users)} users")
        
        # Форматируем данные для ответа
        users_data = []
        for user in users:
            time_diff = (now - user.last_active).total_seconds() if user.last_active else float('inf')
            is_active = time_diff < 300  # 5 минут
            
            user_data = {
                "id": user.telegram_id,
                "username": user.username,
                "last_active": user.last_active.isoformat() if user.last_active else None,
                "is_active": is_active
            }
            users_data.append(user_data)
            
            # Логируем статус каждого пользователя
            logger.info(f"User {user.telegram_id} status: active={is_active}, last_active={user.last_active}")
        
        return {
            "users": users_data
        }
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def update_user_activity(request: Request, call_next):
    """Обновляет время последней активности пользователя."""
    try:
        # Получаем init_data из разных возможных источников
        init_data = None
        if "Telegram-Web-App" in request.headers.get("User-Agent", ""):
            # Пробуем получить из query параметров
            init_data = request.query_params.get("initData")
            if not init_data:
                # Пробуем получить из заголовков
                init_data = request.headers.get("X-Telegram-Init-Data")
                
        if init_data:
            logger.info(f"Received init data: {init_data[:100]}...")  # Логируем для отладки
            user_data = parse_init_data(init_data)
            if user_data and "user" in user_data:
                user_id = user_data["user"].get("id")
                if user_id:
                    logger.info(f"Updating activity for user {user_id}")
                    db = next(get_db())
                    user = db.query(User).filter(User.telegram_id == user_id).first()
                    if user:
                        user.last_active = datetime.now(timezone.utc)
                        db.commit()
                        logger.info(f"Activity updated for user {user_id}")
                    else:
                        logger.warning(f"User {user_id} not found in database")
    except Exception as e:
        logger.error(f"Error in activity middleware: {e}")
    
    response = await call_next(request)
    return response 