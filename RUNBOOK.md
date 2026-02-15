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

## API commands (for diagnostics)
```bash
# DaData
curl -s https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $DADATA_API_KEY" \
  -d '{"query":"3525405517"}'

# Checko company
curl -s "https://api.checko.ru/v2/company?key=$CHECKO_API_KEY&inn=3525405517"

# Checko sections
curl -s "https://api.checko.ru/v2/finances?key=$CHECKO_API_KEY&inn=3525405517"
curl -s "https://api.checko.ru/v2/legal-cases?key=$CHECKO_API_KEY&inn=3525405517"
curl -s "https://api.checko.ru/v2/enforcements?key=$CHECKO_API_KEY&inn=3525405517"
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
