from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

CB = {
    "home": "nav:home",
    "back": "nav:back",
    "successor": "page:successor",
    "contacts": "page:contacts",
    "authorities": "page:authorities",
    "new_inn": "page:new_inn",
    "menu": "page:menu",
    "finance": "page:finance",
    "cases": "page:cases",
    "founders": "page:founders",
    "contracts": "page:contracts",
    "taxes": "page:taxes",
    "debts": "page:debts",
    "inspections": "page:inspections",
    "pdf": "act:pdf",
}


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
            InlineKeyboardButton(text="Правопреемник", callback_data=CB["successor"]),
            InlineKeyboardButton(text="Все контакты", callback_data=CB["contacts"]),
        ],
        [
            InlineKeyboardButton(text="ФНС/ПФР/ФСС/Росстат", callback_data=CB["authorities"]),
            InlineKeyboardButton(text="Новый ИНН", callback_data=CB["new_inn"]),
            InlineKeyboardButton(text="Меню", callback_data=CB["menu"]),
        ],
        [
            InlineKeyboardButton(text="Финансы", callback_data=CB["finance"]),
            InlineKeyboardButton(text="Суды", callback_data=CB["cases"]),
            InlineKeyboardButton(text="Учредители", callback_data=CB["founders"]),
        ],
        [
            InlineKeyboardButton(text="Госзакупки", callback_data=CB["contracts"]),
            InlineKeyboardButton(text="Налоги", callback_data=CB["taxes"]),
            InlineKeyboardButton(text="Долги", callback_data=CB["debts"]),
            InlineKeyboardButton(text="Проверки", callback_data=CB["inspections"]),
        ],
        [InlineKeyboardButton(text="сохранить в pdf", callback_data=CB["pdf"])],
        _nav_row(),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subpage_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[_nav_row()])


def _nav_row() -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(text="назад", callback_data=CB["back"]),
        InlineKeyboardButton(text="домой", callback_data=CB["home"]),
    ]
