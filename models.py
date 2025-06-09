from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

# Таблица для связи многие-ко-многим между пользователями и мероприятиями (сохраненные)
saved_events = Table('saved_events', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('event_id', Integer, ForeignKey('events.id'))
)

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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_active = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    subscribed_events = relationship("Event", secondary=event_subscribers, back_populates="subscribers")
    saved_events = relationship("Event", secondary=saved_events, back_populates="saved_by")
    reminders = relationship("Reminder", back_populates="user")
    votes = relationship("Vote", back_populates="user")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    date = Column(DateTime(timezone=True))
    location = Column(String)
    category = Column(String)  # meeting, concert, exhibition, sport, other
    max_participants = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey('users.id'))
    
    subscribers = relationship("User", secondary=event_subscribers, back_populates="subscribed_events")
    saved_by = relationship("User", secondary=saved_events, back_populates="saved_events")
    reminders = relationship("Reminder", back_populates="event")

class Reminder(Base):
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    reminder_time = Column(Integer)  # время в минутах до начала мероприятия
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="reminders")
    event = relationship("Event", back_populates="reminders")

class Poll(Base):
    __tablename__ = 'polls'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey('users.id'))
    
    options = relationship("PollOption", back_populates="poll")

class PollOption(Base):
    __tablename__ = 'poll_options'
    
    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey('polls.id'))
    text = Column(String)
    
    poll = relationship("Poll", back_populates="options")
    votes = relationship("Vote", back_populates="option")

class Vote(Base):
    __tablename__ = 'votes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    poll_id = Column(Integer, ForeignKey('polls.id'))
    option_id = Column(Integer, ForeignKey('poll_options.id'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="votes")
    option = relationship("PollOption", back_populates="votes") 