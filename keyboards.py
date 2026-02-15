"""Инлайн-клавиатуры бота."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CB_SHOW_REQ = "show_requisites"
CB_SHOW_FIN = "show_finances"
CB_SHOW_CASES = "show_cases"
CB_SHOW_DEBTS = "show_debts"
CB_SHOW_INSPECTIONS = "show_inspections"
CB_SHOW_CONTRACTS = "show_contracts"
CB_BACK = "nav_back"
CB_HOME = "nav_home"


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Помощь", callback_data=CB_HOME)],
        ]
    )


def section_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Реквизиты", callback_data=CB_SHOW_REQ),
                InlineKeyboardButton(text="Финансы", callback_data=CB_SHOW_FIN),
            ],
            [
                InlineKeyboardButton(text="Суды", callback_data=CB_SHOW_CASES),
                InlineKeyboardButton(text="Долги", callback_data=CB_SHOW_DEBTS),
            ],
            [
                InlineKeyboardButton(text="Проверки", callback_data=CB_SHOW_INSPECTIONS),
                InlineKeyboardButton(text="Госзакупки", callback_data=CB_SHOW_CONTRACTS),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=CB_BACK),
                InlineKeyboardButton(text="🏠 Домой", callback_data=CB_HOME),
            ],
        ]
    )


def back_home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=CB_BACK),
                InlineKeyboardButton(text="🏠 Домой", callback_data=CB_HOME),
            ]
        ]
    )
