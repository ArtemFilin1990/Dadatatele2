# Telegram-бот «Проверка контрагента» (aiogram v3)

Бот проверяет контрагента по ИНН и объединяет источники:
- **Checko** — юридическая база и риск-контекст (истина: идентификация/статус/адрес/правопреемник).
- **DaData** — обогащение (контакты, быстрый паспорт).
- **Локальные справочники** (`db/reference_data.sqlite`) — расшифровки кодов.

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python tools/build_reference_db.py
python -m src.main
```

## ENV
```env
TELEGRAM_BOT_TOKEN=
CHECKO_API_KEY=
DADATA_API_KEY=
DADATA_SECRET=
CACHE_TTL_SECONDS=21600
STRICT_INN_CHECK=false
LOG_LEVEL=INFO
```

## Endpoint map
- DaData `POST /suggestions/api/4_1/rs/findById/party`.
- Checko:
  - `GET /v2/company?key=...&inn=<10>`
  - `GET /v2/entrepreneur?key=...&inn=<12>`
  - `GET /v2/person?key=...&inn=<12>` (fallback)
  - `GET /v2/finances?key=...&inn=...`
  - `GET /v2/legal-cases?key=...&inn=...`
  - `GET /v2/enforcements?key=...&inn=...`
  - `GET /v2/inspections?key=...&inn=...`
  - `GET /v2/contracts?key=...&inn=...`

## UX
- `/start` и кнопки: `[🏁 Старт][👋 Привет]` + `[🔎 Проверить ИНН]`.
- Валидация ИНН:
  - только цифры,
  - длина 10 или 12,
  - при `STRICT_INN_CHECK=true` — контрольная сумма.
- После валидного ИНН: карточка + inline-разделы.
- На каждом экране фиксированный нижний ряд: **[назад] [домой]**.

## Кэш
SQLite TTL-кэш в `db/cache.sqlite`.
TTL:
- company/entrepreneur/person — 24h
- finances — 7d
- contracts — 24h
- legal-cases — 24h
- enforcements — 12h
- inspections — 7d

## Справочники
`tools/build_reference_db.py` создаёт:
- `db/reference_data.sqlite`
- `db/cache.sqlite`

и пытается импортировать ZIP-файлы из `assets/reference_sources/`:
- `statuses.xlsx.zip`, `okved_2.sql.zip`, `okopf.sql.zip`, `okfs.sql.zip`, `okpd.sql.zip`, `okpd_2.sql.zip`, `account_codes.sql.zip`.

## [[TBD]]
- Точные названия некоторых полей в ответах Checko зависят от версии/тарифа API; используется defensive parsing (`dict.get`).
- Если в `assets/reference_sources/` нет zip-файлов, база справочников создаётся пустой (схема сохранена).
