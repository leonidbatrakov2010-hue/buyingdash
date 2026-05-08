# Buying Dashboard

Веб-дашборд для арбитражной команды. Получает данные от Telegram-бота и показывает красивый дашборд.

## Деплой на Railway

1. Загрузи эту папку на GitHub
2. Зайди на railway.app
3. New Project → Deploy from GitHub repo
4. Выбери репозиторий
5. В Settings → Variables добавь:
   - `API_SECRET` = любой секретный ключ (например `myteam2024`)
6. Railway автоматически даст домен

## Переменные окружения

- `API_SECRET` — секрет для защиты API (должен совпадать с ботом)
- `PORT` — Railway устанавливает автоматически

## API

POST `/api/report` — принять отчет от бота
GET  `/api/reports?days=7` — получить отчеты
GET  `/` — дашборд
