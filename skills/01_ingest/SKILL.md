# Skill: ingest

## Назначение
Собрать и подготовить входные данные из архива и XLSX/CSV источников.

## Входы
- catalog_full_brands_aprom_enriched.xlsx
- catalog_full_brands_aprom_patch.xlsx
- scraped_data.json
- brands.json

## Шаги
1. Прочитать источники истины (`REF_GOST_ISO_размеры`, `REF_ISO_суффиксы`, `MASTER_PRODUCTS`).
2. Собрать список рабочих таблиц брендов и карточек.
3. Привести названия колонок к ожидаемым рабочим полям.
4. Отфильтровать технические/служебные листы (`DICT_*`, `CROSSREF_*`, `SCHEMA*`).

## Выход
Набор датафреймов/таблиц, готовых к нормализации.
