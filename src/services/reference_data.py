from __future__ import annotations


OKVED_FALLBACK = {
    "46.90": "Торговля оптовая неспециализированная",
    "62.01": "Разработка компьютерного программного обеспечения",
    "41.20": "Строительство жилых и нежилых зданий",
}


def decode_okved(code: str) -> str:
    if not code:
        return "—"
    return OKVED_FALLBACK.get(code, "расшифровка не найдена")
