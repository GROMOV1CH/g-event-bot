import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButton, WebAppInfo, MenuButtonWebApp
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import settings
from datetime import datetime
from models import User, Event, Reminder, Poll
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import asyncio
import os
import jwt
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo
from sqlalchemy.orm import sessionmaker
from models import Base

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Изменили уровень логирования на DEBUG
)
logger = logging.getLogger(__name__)

logger.info("Starting bot initialization...")
logger.info(f"Bot token: {settings.BOT_TOKEN[:5]}...")
logger.info(f"Database URL: {settings.DATABASE_URL}")
logger.info(f"Webapp URL: {settings.WEBAPP_URL}")
logger.info(f"Admin IDs: {settings.ADMIN_USER_IDS}")

# Инициализация базы данных
engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)

# Генерация JWT токена
def generate_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    logger.debug("Entering start handler")
    logger.info(f"Start command received from user {update.effective_user.id}")
    try:
        db = SessionLocal()
        # Проверяем, существует ли пользователь
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            # Создаем нового пользователя
            user = User(telegram_id=update.effective_user.id)
            db.add(user)
            db.commit()
        
        # Создаем кнопку для открытия веб-приложения
        webapp_button = types.InlineKeyboardButton(
            text="Открыть приложение",
            web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}?token={generate_token(update.effective_user.id)}")
        )
        keyboard = types.InlineKeyboardMarkup().add(webapp_button)
        
        await update.message.reply_text(
            "Добро пожаловать в бот для управления мероприятиями и опросами! ��\n\n"
            "Здесь вы можете:\n"
            "📅 Просматривать предстоящие мероприятия\n"
            "📜 Смотреть прошедшие мероприятия\n"
            "📊 Участвовать в опросах\n"
            "🗳️ Видеть результаты голосований\n\n"
            "Нажмите кнопку ниже, чтобы открыть приложение:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}")
        raise

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    logger.debug("Entering button handler")
    query = update.callback_query
    await query.answer()
    
    logger.info(f"Button {query.data} pressed by user {update.effective_user.id}")
    
    try:
        if query.data == "my_subscriptions":
            logger.debug("Handling my_subscriptions")
            await query.message.reply_text("Ваши подписки на мероприятия:")
        elif query.data == "help":
            logger.debug("Handling help")
            await query.message.reply_text(
                "Это бот для управления мероприятиями. "
                "Вы можете просматривать предстоящие мероприятия, "
                "подписываться на уведомления и получать напоминания. "
                "\n\nНажмите кнопку 'Открыть приложение' внизу экрана, "
                "чтобы открыть веб-интерфейс."
            )
        elif query.data == "admin_panel" and update.effective_user.id in settings.ADMIN_USER_IDS:
            logger.debug("Handling admin_panel")
            admin_keyboard = [
                [InlineKeyboardButton("Создать мероприятие", callback_data="create_event")],
                [InlineKeyboardButton("Управление мероприятиями", callback_data="manage_events")]
            ]
            await query.message.reply_text(
                "Панель администратора:",
                reply_markup=InlineKeyboardMarkup(admin_keyboard)
            )
    except Exception as e:
        logger.error(f"Error in button handler: {str(e)}")
        raise

async def check_reminders():
    """Проверка и отправка напоминаний"""
    logger.debug("Checking reminders")
    with Session(engine) as session:
        current_time = datetime.utcnow()
        reminders = session.query(Reminder).filter(
            Reminder.remind_at <= current_time,
            Reminder.sent == False
        ).all()
        
        for reminder in reminders:
            logger.debug(f"Processing reminder {reminder.id}")
            reminder.sent = True
            session.commit()

def main():
    """Запуск бота"""
    logger.info("Initializing bot application...")
    try:
        application = Application.builder().token(settings.BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("Starting bot polling...")
        # Запускаем бота
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise

if __name__ == '__main__':
    main() 