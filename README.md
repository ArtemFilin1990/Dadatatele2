# Telegram-бот «Проверка контрагента»

Бот на `aiogram v3` проверяет контрагента по ИНН и объединяет данные:
- **Checko** — юридическая база и риск-контекст.
- **DaData** — быстрый паспорт/контакты.

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## .env
```env
TELEGRAM_BOT_TOKEN=
TG_BOT_TOKEN=  # optional alias for TELEGRAM_BOT_TOKEN
CHECKO_API_KEY=
DADATA_API_KEY=
DADATA_SECRET=
CACHE_TTL_SECONDS=21600
STRICT_INN_CHECK=false
LOG_LEVEL=INFO
```

## Что умеет
- `/start` + reply-кнопки `🏁 Старт`, `👋 Привет`, `🔎 Проверить ИНН`.
- Валидация ИНН: только цифры, длина 10/12; опционально контрольная сумма (`STRICT_INN_CHECK=true`).
- Токен бота читается из `TELEGRAM_BOT_TOKEN` или совместимого алиаса `TG_BOT_TOKEN`.
- Карточка контрагента + inline-разделы.
- На всех inline-экранах неизменная нижняя строка: **[назад] [домой]**.
- Разделы: Финансы, Суды, Долги + базовые остальные.
- Экспорт карточки в PDF.

## Архитектура
```
src/
  main.py
  bot/
    handlers.py
    keyboards.py
    states.py
    formatters.py
  clients/
    dadata.py
    checko.py
  services/
    aggregator.py
    cache.py
    reference_data.py
    inn.py
    settings.py
  storage/
    session_store.py
tools/
  build_reference_db.py
tests/
  test_inn.py
  test_formatters.py
```

## Справочники
Скрипт `tools/build_reference_db.py` создаёт пустой `reference_data.db` и схему таблиц (`okved2`, `okopf`, `okfs`, `okpd`, `okpd2`, `account_codes`, `statuses`) для последующего импорта ваших SQL/XLSX файлов.

## ASSUMPTIONS
- В текущей реализации Checko-запросы сделаны через `GET` (как основной путь).
- Для раздела «Финансы» используется endpoint `/v2/finance` (по присланному ТЗ).
- Если `reportlab` недоступен, экспорт возвращает текст как байты (fallback).
