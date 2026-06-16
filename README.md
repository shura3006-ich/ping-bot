# Ping Monitor Bot

Telegram бот который мониторит серверы и шлёт алерты когда сервер падает или поднимается.

## Переменные окружения (задать в Railway)

| Переменная | Значение |
|---|---|
| `TELEGRAM_TOKEN` | Токен от @BotFather |
| `CHAT_ID` | Твой Telegram ID |
| `CHECK_INTERVAL` | Интервал проверки в секундах (по умолчанию 60) |

## Деплой на Railway

1. Залей эту папку на GitHub
2. Зайди на railway.app → New Project → Deploy from GitHub
3. Добавь переменные окружения
4. Railway сам запустит бота
