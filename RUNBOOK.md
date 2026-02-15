# RUNBOOK

## Prereqs
- Python 3.11+
- Доступ к: `api.telegram.org`, `api.checko.ru`, `suggestions.dadata.ru`

## Старт
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python tools/build_reference_db.py
python -m src.main
```

## Smoke
1. `/start` -> кнопки меню
2. `🔎 Проверить ИНН` -> запрос ввода
3. Ввод `3525405517` -> карточка
4. Открыть `Финансы`, `Суды`, `Долги`
5. Проверить `[назад]` и `[домой]` на каждом экране

## Тесты
```bash
pytest -q
```
