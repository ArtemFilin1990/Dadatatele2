# TEST REPORT

## Passed
- Реализованы `/start`, reply-меню и сценарий проверки ИНН.
- Реализованы клиенты DaData/Checko с retry+backoff и timeout 15s.
- Реализован агрегатор (Checko приоритет + DaData fallback/enrichment, дедуп контактов).
- Реализованы разделы и неизменный нижний ряд `[назад] [домой]`.
- Реализованы SQLite cache (`db/cache.sqlite`) и сборка справочников (`db/reference_data.sqlite`).
- Unit tests проходят.

## [[TBD]]
- Полный e2e Telegram/API в этом контейнере ограничен сетью окружения.
- Импорт справочников требует наличия ZIP-файлов в `assets/reference_sources/`.
