# INN Checker Bot

Telegram-бот для проверки ИНН через DaData.

## Возможности
- Проверка и нормализация ИНН (10/12 цифр) с контролем контрольной суммы.
- Поиск организации/ИП по ИНН через прямой вызов DaData API.
- Режим `OpenAI + MCP` реализован как безопасный fallback на прямой DaData-клиент до подключения подтверждённого MCP transport.

## Быстрый старт
```bash
cd inn_checker_bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env`, затем запустите:
```bash
python bot.py
```

## Переменные окружения
- `TELEGRAM_BOT_TOKEN` — токен Telegram-бота (обязательно).
- `DADATA_API_TOKEN` — API токен DaData (обязательно).
- `DADATA_API_SECRET` — секрет DaData (опционально).
- `OPENAI_API_KEY` — ключ OpenAI (опционально, сейчас не используется в runtime).
- `OPENAI_MODEL` — модель OpenAI (по умолчанию `gpt-4.1-mini`).
- `REQUEST_TIMEOUT_SECONDS` — таймаут HTTP-запросов в секундах (по умолчанию `10`).

## Структура
```text
inn_checker_bot/
├── bot.py
├── config.py
├── handlers.py
├── keyboards.py
├── validators.py
├── dadata_direct.py
├── dadata_mcp.py
├── requirements.txt
├── .env.example
└── README.md
```
