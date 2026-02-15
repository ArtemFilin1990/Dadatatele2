"""Обработчики команд и сообщений бота."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from checko_client import checko_client
from enrichment import build_profile, render_section, render_summary
from keyboards import (
    CB_BACK,
    CB_HOME,
    CB_SHOW_CASES,
    CB_SHOW_CONTRACTS,
    CB_SHOW_DEBTS,
    CB_SHOW_FIN,
    CB_SHOW_INSPECTIONS,
    CB_SHOW_REQ,
    back_home_kb,
    main_menu_kb,
    section_menu_kb,
)
from validators import parse_inns, validate_inn

logger = logging.getLogger(__name__)
router = Router()


class CheckINN(StatesGroup):
    waiting_inn = State()


RATE_WINDOW_SECONDS = 5
RATE_LIMIT_MESSAGES = 8
_chat_messages: dict[int, deque[float]] = defaultdict(deque)

WELCOME_TEXT = (
    "<b>Проверка компаний по ИНН</b>\n\n"
    "Истина и риски: <b>Checko</b>.\n"
    "Контакты/подсказки: <b>DaData</b>.\n"
    "Введите ИНН (10 цифр — юрлицо, 12 — ИП/физлицо)."
)


def _spam_limited(chat_id: int) -> bool:
    now = time.time()
    q = _chat_messages[chat_id]
    while q and now - q[0] > RATE_WINDOW_SECONDS:
        q.popleft()
    q.append(now)
    return len(q) > RATE_LIMIT_MESSAGES


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CheckINN.waiting_inn)
    await message.answer(WELCOME_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())


@router.callback_query(F.data == CB_HOME)
async def on_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CheckINN.waiting_inn)
    await callback.message.edit_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == CB_BACK)
async def on_back(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    summary = data.get("last_summary")
    if not summary:
        await callback.answer("Нет предыдущего экрана", show_alert=False)
        return
    await callback.message.edit_text(summary, parse_mode="HTML", reply_markup=section_menu_kb())
    await callback.answer()


@router.message(CheckINN.waiting_inn)
async def on_inn(message: Message, state: FSMContext) -> None:
    if _spam_limited(message.chat.id):
        await message.answer("⚠️ Слишком часто. Подождите пару секунд.")
        return

    tokens = parse_inns(message.text or "")
    if not tokens:
        await message.answer("⚠️ Введите ИНН (10 или 12 цифр).")
        return

    for token in tokens[:5]:
        is_valid, desc = validate_inn(token)
        if not is_valid:
            await message.answer(f"⚠️ <code>{token}</code> — {desc}", parse_mode="HTML")
            continue

        wait_message = await message.answer(f"⏳ Загружаю профиль по ИНН <code>{token}</code>…", parse_mode="HTML")
        profile = await build_profile(token)
        if profile is None:
            await wait_message.edit_text(
                f"❌ По ИНН <code>{token}</code> данные не найдены ни в Checko, ни в DaData.",
                parse_mode="HTML",
                reply_markup=back_home_kb(),
            )
            continue

        summary = render_summary(profile)
        await state.update_data(current_inn=token, current_type=profile.entity_type, last_summary=summary)
        await wait_message.edit_text(summary, parse_mode="HTML", reply_markup=section_menu_kb())

    await message.answer("Можно отправить ещё ИНН.", reply_markup=back_home_kb())


async def _section(callback: CallbackQuery, state: FSMContext, section: str) -> None:
    data = await state.get_data()
    inn = data.get("current_inn")
    entity_type = data.get("current_type")
    if not inn:
        await callback.answer("Сначала отправьте ИНН", show_alert=False)
        return

    if section == "req":
        text = data.get("last_summary") or "Нет данных"
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=section_menu_kb())
        await callback.answer()
        return

    loaders = {
        "fin": ("Финансы", checko_client.fetch_finances),
        "cases": ("Суды", checko_client.fetch_legal_cases),
        "debts": ("Долги (ФССП)", checko_client.fetch_enforcements),
        "inspections": ("Проверки", checko_client.fetch_inspections),
        "contracts": ("Госзакупки", checko_client.fetch_contracts),
    }
    title, loader = loaders[section]
    payload = await loader(inn)
    if payload and isinstance(payload, dict):
        payload = {"entity_type": entity_type, **payload}
    text = render_section(title, payload)
    if section == "debts":
        text += "\n\nℹ️ ФССП иногда даёт ложные совпадения по названию/адресу."
    if section == "cases":
        text += "\n\nℹ️ Судебные данные могут иметь задержку до 1–2 недель."
    if section == "contracts":
        text += "\n\nℹ️ По 223-ФЗ после 2019 данные о поставщиках могут быть неполными."

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_home_kb())
    await callback.answer()


@router.callback_query(F.data == CB_SHOW_REQ)
async def on_req(callback: CallbackQuery, state: FSMContext) -> None:
    await _section(callback, state, "req")


@router.callback_query(F.data == CB_SHOW_FIN)
async def on_fin(callback: CallbackQuery, state: FSMContext) -> None:
    await _section(callback, state, "fin")


@router.callback_query(F.data == CB_SHOW_CASES)
async def on_cases(callback: CallbackQuery, state: FSMContext) -> None:
    await _section(callback, state, "cases")


@router.callback_query(F.data == CB_SHOW_DEBTS)
async def on_debts(callback: CallbackQuery, state: FSMContext) -> None:
    await _section(callback, state, "debts")


@router.callback_query(F.data == CB_SHOW_INSPECTIONS)
async def on_inspections(callback: CallbackQuery, state: FSMContext) -> None:
    await _section(callback, state, "inspections")


@router.callback_query(F.data == CB_SHOW_CONTRACTS)
async def on_contracts(callback: CallbackQuery, state: FSMContext) -> None:
    await _section(callback, state, "contracts")
