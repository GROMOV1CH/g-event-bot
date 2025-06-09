from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# Таблица связи пользователей и мероприятий (для подписок)
event_subscribers = Table(
    'event_subscribers',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('event_id', Integer, ForeignKey('events.id'))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    is_admin = Column(Boolean, default=False)
    subscribed_events = relationship("Event", secondary=event_subscribers, back_populates="subscribers")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    location = Column(String)
    category = Column(String)
    max_participants = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    subscribers = relationship("User", secondary=event_subscribers, back_populates="subscribed_events")
    reminders = relationship("Reminder", back_populates="event")

class Reminder(Base):
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    remind_at = Column(DateTime, nullable=False)
    sent = Column(Boolean, default=False)
    
    event = relationship("Event", back_populates="reminders") 