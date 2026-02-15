# RUNBOOK

## Prereqs
- Python 3.11+
- Доступ к: `api.telegram.org`, `api.checko.ru`, `suggestions.dadata.ru`

## ENV
См. `.env.example`.

## Запуск
```bash
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## Smoke
1. `/start`
2. Нажать `👋 Привет`
3. Нажать `🔎 Проверить ИНН`
4. Отправить валидный ИНН, например `3525405517`
5. Проверить открытие разделов (`Финансы`, `Суды`, `Долги`) и навигацию `[назад] [домой]`

## Тесты
```bash
pytest -q
```
