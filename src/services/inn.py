from __future__ import annotations

import re


def validate_inn(inn: str, strict: bool = False) -> tuple[bool, str]:
    value = inn.strip()
    if not re.fullmatch(r"\d+", value):
        return False, "Похоже, это не ИНН 🙂 Нужны только цифры без пробелов."
    if len(value) not in {10, 12}:
        return False, "ИНН должен быть из 10 или 12 цифр. Пример: 3525405517"
    if strict and not _check_checksum(value):
        return False, "Контрольная сумма не сходится. Проверь цифры (или отключи строгую проверку)."
    return True, "ok"


def _check_checksum(inn: str) -> bool:
    digits = [int(x) for x in inn]
    if len(digits) == 10:
        coef = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        control = sum(a * b for a, b in zip(coef, digits[:9])) % 11 % 10
        return control == digits[9]
    if len(digits) == 12:
        c1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        k1 = sum(a * b for a, b in zip(c1, digits[:10])) % 11 % 10
        c2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        k2 = sum(a * b for a, b in zip(c2, digits[:11])) % 11 % 10
        return k1 == digits[10] and k2 == digits[11]
    return False
