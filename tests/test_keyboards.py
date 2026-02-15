from src.bot.keyboards import card_inline_kb, start_kb


def test_start_keyboard_has_expected_buttons():
    kb = start_kb()
    labels = [[button.text for button in row] for row in kb.keyboard]

    assert labels == [["🏁 Старт", "👋 Привет"], ["🔎 Проверить ИНН"]]


def test_card_inline_keyboard_ends_with_navigation_row():
    kb = card_inline_kb()
    nav_row = kb.inline_keyboard[-1]

    assert [button.text for button in nav_row] == ["назад", "домой"]
