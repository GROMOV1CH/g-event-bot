# Telegram Event Manager Bot

Telegram бот для управления мероприятиями и опросами с веб-интерфейсом.

## Возможности

- Создание и управление мероприятиями
- Система опросов
- Фильтрация и поиск мероприятий
- Напоминания о мероприятиях
- Сохранение избранных мероприятий
- Статистика для администраторов

## Технологии

- Python 3.8+
- FastAPI
- SQLAlchemy
- Telegram Bot API
- HTML/CSS/JavaScript

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/tgbot-event-manager.git
cd tgbot-event-manager
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` и добавьте необходимые переменные окружения:
```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///./events.db
ADMIN_ID=your_telegram_id
```

5. Запустите приложение:
```bash
uvicorn webapp:app --reload
```

## Использование

1. Откройте бота в Telegram
2. Следуйте инструкциям для создания мероприятий или участия в них
3. Используйте веб-интерфейс для расширенного управления

## Разработка

Проект использует:
- FastAPI для backend API
- SQLAlchemy для работы с базой данных
- Vanilla JavaScript для frontend
- Telegram Bot API для взаимодействия с Telegram

## Лицензия

MIT
