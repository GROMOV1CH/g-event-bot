# Telegram Event Management Bot

Бот для управления мероприятиями с веб-интерфейсом.

## Локальный запуск

1. Создайте файл `.env` и добавьте необходимые переменные:
```
BOT_TOKEN=ваш_токен_бота
ADMIN_USER_IDS=id1,id2
DATABASE_URL=sqlite:///./events.db
WEBAPP_URL=https://ваш-домен/webapp
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите бота:
```bash
python bot.py
```

4. В отдельном терминале запустите веб-приложение:
```bash
uvicorn webapp:app --reload
```

## Деплой на Render.com

1. Создайте аккаунт на Render.com
2. Подключите ваш GitHub репозиторий
3. Создайте новый Web Service
4. Укажите следующие переменные окружения:
   - BOT_TOKEN
   - ADMIN_USER_IDS
   - DATABASE_URL (используйте PostgreSQL от Render)
   - WEBAPP_URL (будет доступен после деплоя)

## Структура проекта

- `bot.py` - основной файл бота
- `webapp.py` - FastAPI веб-приложение
- `models.py` - модели базы данных
- `config.py` - конфигурация
- `gunicorn_config.py` - настройки Gunicorn
- `render.yaml` - конфигурация для Render.com

## Функционал

- Просмотр предстоящих и прошедших мероприятий
- Система подписки на мероприятия
- Автоматические напоминания
- Панель администратора для управления мероприятиями
- Веб-интерфейс для удобного просмотра

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd event-manager-bot
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

4. Создайте файл `.env` на основе `.env.example` и заполните необходимые переменные:
```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///./events.db
WEBAPP_URL=https://your-webapp-url.com
ADMIN_USER_IDS=123456789,987654321
```

## Запуск

1. Запустите веб-приложение:
```bash
python webapp.py
```

2. В отдельном терминале запустите бота:
```bash
python bot.py
```

## Использование

1. Найдите бота в Telegram по его имени
2. Отправьте команду `/start`
3. Следуйте инструкциям в меню бота

## Для администраторов

1. Добавьте свой Telegram ID в переменную `ADMIN_USER_IDS` в файле `.env`
2. Перезапустите бота
3. Используйте панель администратора для управления мероприятиями

## Разработка

- `models.py` - модели базы данных
- `bot.py` - логика телеграм бота
- `webapp.py` - FastAPI веб-приложение
- `config.py` - конфигурация приложения 