from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from src.bot import callbacks as cb


def start_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏁 Старт"), KeyboardButton(text="👋 Привет")],
            [KeyboardButton(text="🔎 Проверить ИНН")],
        ],
        resize_keyboard=True,
    )


def card_inline_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Правопреемник", callback_data=cb.PAGE_SUCCESSOR),
            InlineKeyboardButton(text="Все контакты", callback_data=cb.PAGE_CONTACTS),
        ],
        [
            InlineKeyboardButton(text="ФНС/ПФР/ФСС/Росстат", callback_data=cb.PAGE_AUTHORITIES),
            InlineKeyboardButton(text="Новый ИНН", callback_data=cb.PAGE_NEW_INN),
            InlineKeyboardButton(text="Меню", callback_data=cb.PAGE_MENU),
        ],
        [
            InlineKeyboardButton(text="Финансы", callback_data=cb.PAGE_FINANCE),
            InlineKeyboardButton(text="Суды", callback_data=cb.PAGE_CASES),
            InlineKeyboardButton(text="Учредители", callback_data=cb.PAGE_FOUNDERS),
        ],
        [
            InlineKeyboardButton(text="Госзакупки", callback_data=cb.PAGE_CONTRACTS),
            InlineKeyboardButton(text="Налоги", callback_data=cb.PAGE_TAXES),
            InlineKeyboardButton(text="Долги", callback_data=cb.PAGE_DEBTS),
            InlineKeyboardButton(text="Проверки", callback_data=cb.PAGE_INSPECTIONS),
        ],
        [InlineKeyboardButton(text="сохранить в pdf", callback_data=cb.ACT_PDF)],
        _nav_row(),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subpage_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[_nav_row()])


def _nav_row() -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(text="назад", callback_data=cb.NAV_BACK),
        InlineKeyboardButton(text="домой", callback_data=cb.NAV_HOME),
    ]
