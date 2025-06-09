# Telegram Event Management Bot

Бот для управления мероприятиями и опросами в Telegram с веб-интерфейсом.

## Возможности

- 📅 Управление мероприятиями (создание, редактирование, удаление)
- 📊 Создание и проведение опросов
- 👥 Система пользователей и администраторов
- 🌐 Современный веб-интерфейс
- 📱 Адаптивный дизайн для всех устройств

## Технологии

- FastAPI для бэкенда
- SQLAlchemy для работы с базой данных
- Telegram Bot API и Web App
- HTML/CSS/JavaScript для фронтенда
- SQLite для хранения данных

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/tgbot-events.git
cd tgbot-events
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
pip install -r requirements.txt
```

3. Создайте файл .env с необходимыми переменными окружения:
```
BOT_TOKEN=your_bot_token
WEBAPP_URL=your_webapp_url
JWT_SECRET=your_jwt_secret
BOT_OWNER_ID=your_telegram_id
```

4. Примените миграции базы данных:
```bash
alembic upgrade head
```

5. Запустите приложение:
```bash
uvicorn webapp:app --reload
```

## Использование

1. Добавьте бота в Telegram и отправьте команду /start
2. Нажмите на кнопку "Открыть приложение" для доступа к веб-интерфейсу
3. Используйте команду /admin <user_id> для назначения администраторов (только для владельца бота)

## Структура проекта

- `bot.py` - Основной файл бота
- `webapp.py` - FastAPI веб-приложение
- `models.py` - Модели SQLAlchemy
- `static/` - Статические файлы (CSS, JavaScript)
- `templates/` - HTML шаблоны
- `migrations/` - Миграции базы данных

## Лицензия

MIT
