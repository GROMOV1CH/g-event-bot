from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table, JSON
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
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    is_admin = Column(Boolean, default=False)
    subscribed_events = relationship("Event", secondary=event_subscribers, back_populates="subscribers")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    date = Column(DateTime, nullable=False)
    location = Column(String)
    category = Column(String)
    max_participants = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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

class Poll(Base):
    __tablename__ = 'polls'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    end_date = Column(DateTime, nullable=False)
    options = Column(JSON, nullable=False)  # [{text: string, votes: number}]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Vote(Base):
    __tablename__ = 'votes'

    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey('polls.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    option_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    poll = relationship("Poll")
    user = relationship("User") 