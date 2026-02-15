from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from dadata_direct import DaDataDirectClient
from dadata_mcp import DaDataMCPClient
from keyboards import search_mode_keyboard
from validators import parse_and_validate_inn

router = Router()


class InnLookupStates(StatesGroup):
    waiting_mode = State()
    waiting_inn = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(InnLookupStates.waiting_mode)
    await message.answer(
        "Привет! Я помогу проверить ИНН через DaData. Выберите режим поиска:",
        reply_markup=search_mode_keyboard(),
    )


@router.callback_query(F.data.startswith("mode:"))
async def on_mode_selected(callback: CallbackQuery, state: FSMContext) -> None:
    selected_mode = callback.data.split(":", 1)[1]
    if selected_mode not in {"direct", "mcp"}:
        await callback.answer("Неизвестный режим", show_alert=True)
        return

    await state.update_data(mode=selected_mode)
    await state.set_state(InnLookupStates.waiting_inn)
    await callback.message.answer("Введите ИНН (10 или 12 цифр):")
    await callback.answer()


@router.message(InnLookupStates.waiting_inn)
async def on_inn_received(
    message: Message,
    state: FSMContext,
    direct_client: DaDataDirectClient,
    mcp_client: DaDataMCPClient,
) -> None:
    is_valid, inn, error = parse_and_validate_inn(message.text or "")
    if not is_valid:
        await message.answer(f"Ошибка: {error}\nПопробуйте снова.")
        return

    data = await state.get_data()
    mode = data.get("mode", "direct")

    try:
        if mode == "mcp":
            result = await mcp_client.find_party_by_inn(inn)
        else:
            result = await direct_client.find_party_by_inn(inn)
    except Exception:
        await message.answer("Не удалось выполнить запрос. Попробуйте позже.")
        return

    if result is None:
        await message.answer("По этому ИНН ничего не найдено.")
        return

    text = (
        f"Найдено ({result.source}):\n"
        f"• ИНН: {result.inn}\n"
        f"• Название: {result.name}\n"
        f"• КПП: {result.kpp or '—'}\n"
        f"• ОГРН: {result.ogrn or '—'}\n"
        f"• Адрес: {result.address or '—'}"
    )
    await message.answer(text)
