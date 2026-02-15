from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def search_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Прямой DaData API", callback_data="mode:direct")],
            [InlineKeyboardButton(text="Через OpenAI + MCP", callback_data="mode:mcp")],
        ]
    )
