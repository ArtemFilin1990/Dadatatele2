from __future__ import annotations


def normalize_inn(raw_value: str) -> str:
    """Leave only digits and trim whitespace around the original value."""
    return "".join(ch for ch in raw_value.strip() if ch.isdigit())


def _calculate_control_digit(digits: list[int], coefficients: list[int]) -> int:
    total = sum(d * c for d, c in zip(digits, coefficients))
    return (total % 11) % 10


def is_valid_inn(inn: str) -> bool:
    if not inn.isdigit():
        return False

    if len(inn) == 10:
        digits = [int(ch) for ch in inn]
        checksum = _calculate_control_digit(digits, [2, 4, 10, 3, 5, 9, 4, 6, 8])
        return checksum == digits[9]

    if len(inn) == 12:
        digits = [int(ch) for ch in inn]
        first_checksum = _calculate_control_digit(
            digits,
            [7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0],
        )
        second_checksum = _calculate_control_digit(
            digits,
            [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0],
        )
        return first_checksum == digits[10] and second_checksum == digits[11]

    return False


def parse_and_validate_inn(raw_value: str) -> tuple[bool, str, str]:
    normalized = normalize_inn(raw_value)

    if len(normalized) not in {10, 12}:
        return False, normalized, "ИНН должен содержать 10 или 12 цифр."

    if not is_valid_inn(normalized):
        return False, normalized, "Некорректная контрольная сумма ИНН."

    return True, normalized, ""
