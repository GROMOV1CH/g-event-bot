from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pydantic import BaseModel
from models import Base, Event, User, Reminder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
import os
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Инициализация базы данных
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Pydantic модели
class EventBase(BaseModel):
    title: str
    description: str
    start_date: datetime
    end_date: datetime | None = None
    location: str | None = None
    category: str | None = None
    max_participants: int | None = None

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/events/upcoming", response_model=List[EventResponse])
async def get_upcoming_events(db: Session = Depends(get_db)):
    """Получение списка предстоящих мероприятий"""
    events = db.query(Event).filter(
        Event.start_date >= datetime.utcnow()
    ).order_by(Event.start_date).all()
    return events

@app.get("/events/past", response_model=List[EventResponse])
async def get_past_events(db: Session = Depends(get_db)):
    """Получение списка прошедших мероприятий"""
    events = db.query(Event).filter(
        Event.start_date < datetime.utcnow()
    ).order_by(Event.start_date.desc()).all()
    return events

@app.post("/events", response_model=EventResponse)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Создание нового мероприятия"""
    db_event = Event(
        **event.dict(),
        created_at=datetime.utcnow()
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@app.post("/events/{event_id}/subscribe/{user_id}")
async def subscribe_to_event(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Подписка на мероприятие"""
    event = db.query(Event).filter(Event.id == event_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    
    if not event or not user:
        raise HTTPException(status_code=404, detail="Event or user not found")
    
    if user in event.subscribers:
        raise HTTPException(status_code=400, detail="Already subscribed")
    
    event.subscribers.append(user)
    db.commit()
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return {"message": "Event Management Bot API"}

@app.get("/webapp", response_class=HTMLResponse)
async def webapp(request: Request):
    return {"message": "Web App Interface Coming Soon"}

# Добавляем конфигурацию для gunicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("webapp:app", host="0.0.0.0", port=port, reload=True) 