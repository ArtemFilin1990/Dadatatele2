# Skill: export

## Назначение
Сформировать итоговый Excel-каталог из подтверждённых данных.

## Листы
1. GOST
2. ISO
3. SCHEMA
4. PREFIX_DICT
5. SUFFIX_DICT

## Требования
- Единый порядок колонок для GOST/ISO.
- SCHEMA отражает итоговую структуру.
- PREFIX_DICT: только подтверждённые префиксы.
- SUFFIX_DICT: приоритет REF_ISO_суффиксы + подтверждённые дополнения.

## Выход
`result_catalog.xlsx`.
