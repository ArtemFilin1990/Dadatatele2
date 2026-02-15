from __future__ import annotations

import json
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.formatters import format_card
from src.bot import callbacks as cb
from src.bot.keyboards import card_inline_kb, start_kb, subpage_kb
from src.bot.states import MainState
from src.services.aggregator import AggregatorService
from src.services.inn import validate_inn
from src.services.settings import Settings
from src.services.pdf_export import build_pdf
from src.storage.session_store import SessionStore

router = Router()

_settings: Settings | None = None
_aggregator: AggregatorService | None = None
_sessions: SessionStore | None = None


def configure_handlers(settings: Settings, aggregator: AggregatorService, sessions: SessionStore) -> None:
    global _settings, _aggregator, _sessions
    _settings = settings
    _aggregator = aggregator
    _sessions = sessions


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(MainState.waiting_inn)
    await message.answer(
        "Привет! Пришли ИНН (10 или 12 цифр) — соберу карточку контрагента.",
        reply_markup=start_kb(),
    )


@router.message(F.text == "🏁 Старт")
async def start_button(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)


@router.message(F.text == "👋 Привет")
async def hello_button(message: Message) -> None:
    await message.answer("Рад помочь 🙂 Нажмите «🔎 Проверить ИНН» или просто отправьте ИНН.")


@router.message(F.text == "🔎 Проверить ИНН")
async def check_button(message: Message, state: FSMContext) -> None:
    await state.set_state(MainState.waiting_inn)
    await message.answer("Введите ИНН (10 или 12 цифр). Только цифры.")


@router.message(MainState.waiting_inn)
async def on_inn(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    if _settings is None or _aggregator is None or _sessions is None:
        await message.answer("Сервис не инициализирован")
        return
    valid, error = validate_inn(message.text, strict=_settings.strict_inn_check)
    if not valid:
        await message.answer(error)
        return

    inn = message.text.strip()
    profile, raw = await _aggregator.build_profile(inn)
    if profile is None:
        await message.answer("Не удалось найти контрагента по этому ИНН.")
        return

    card = format_card(profile)
    session = _sessions.get(message.from_user.id)
    session.current_inn = inn
    session.current_card = card
    session.stack = [card]
    session.extra = raw
    _sessions.save(message.from_user.id, session)

    await message.answer(card, reply_markup=card_inline_kb())


@router.callback_query(F.data == cb.NAV_BACK)
async def nav_back(callback: CallbackQuery) -> None:
    if _sessions is None or _aggregator is None:
        await callback.answer("Сервис не инициализирован")
        return
    session = _sessions.get(callback.from_user.id)
    if len(session.stack) > 1:
        session.stack.pop()
    _sessions.save(callback.from_user.id, session)
    await callback.message.edit_text(session.stack[-1], reply_markup=card_inline_kb())
    await callback.answer()


@router.callback_query(F.data == cb.NAV_HOME)
async def nav_home(callback: CallbackQuery) -> None:
    if _sessions is None or _aggregator is None:
        await callback.answer("Сервис не инициализирован")
        return
    session = _sessions.get(callback.from_user.id)
    if not session.current_card:
        await callback.answer("Сначала проверьте ИНН")
        return
    session.stack = [session.current_card]
    _sessions.save(callback.from_user.id, session)
    await callback.message.edit_text(session.current_card, reply_markup=card_inline_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("page:"))
async def page_handler(callback: CallbackQuery) -> None:
    if _sessions is None or _aggregator is None:
        await callback.answer("Сервис не инициализирован")
        return
    session = _sessions.get(callback.from_user.id)
    if not session.current_inn:
        await callback.answer("Сначала проверьте ИНН")
        return

    checko = _aggregator.checko
    inn = session.current_inn

    if callback.data == cb.PAGE_NEW_INN:
        await callback.message.edit_text("Введите новый ИНН (10 или 12 цифр).", reply_markup=subpage_kb())
        await callback.answer()
        return

    if callback.data == cb.PAGE_MENU:
        await callback.message.edit_text("Главное меню доступно в reply-клавиатуре ниже.", reply_markup=subpage_kb())
        await callback.answer()
        return

    if callback.data == cb.PAGE_SUCCESSOR:
        text = f"Правопреемник: {(session.extra.get('checko') or {}).get('Правопреемник', 'нет данных')}"
    elif callback.data == cb.PAGE_CONTACTS:
        text = "Все контакты из карточки и источников уже собраны в основном экране."
    elif callback.data == cb.PAGE_AUTHORITIES:
        text = "ФНС/ПФР/ФСС/Росстат: данные зависят от ответа Checko и тарифа."
    elif callback.data == cb.PAGE_FINANCE:
        text = _dump("Финансы", await checko.fetch_finances(inn))
    elif callback.data == cb.PAGE_CASES:
        text = _dump("Суды", await checko.fetch_legal_cases(inn))
    elif callback.data == cb.PAGE_FOUNDERS:
        text = _dump("Учредители", (session.extra.get("checko") or {}).get("Учред"))
    elif callback.data == cb.PAGE_CONTRACTS:
        text = _dump("Госзакупки", await checko.fetch_contracts(inn))
    elif callback.data == cb.PAGE_TAXES:
        text = _dump("Налоги", (session.extra.get("checko") or {}).get("Налоги"))
    elif callback.data == cb.PAGE_DEBTS:
        text = _dump("Долги", await checko.fetch_enforcements(inn))
    elif callback.data == cb.PAGE_INSPECTIONS:
        text = _dump("Проверки", await checko.fetch_inspections(inn))
    else:
        text = "Раздел недоступен."

    session.stack.append(text)
    _sessions.save(callback.from_user.id, session)
    await callback.message.edit_text(text, reply_markup=subpage_kb())
    await callback.answer()


@router.callback_query(F.data == cb.ACT_PDF)
async def export_pdf(callback: CallbackQuery) -> None:
    if _sessions is None:
        await callback.answer("Сервис не инициализирован")
        return
    session = _sessions.get(callback.from_user.id)
    if not session.current_card:
        await callback.answer("Нет карточки для экспорта")
        return

    data = build_pdf(session.current_card)
    filename = f"counterparty_{session.current_inn or datetime.now().strftime('%Y%m%d')}.pdf"
    await callback.message.answer_document(BufferedInputFile(data, filename=filename))
    await callback.answer("PDF готов")


def _dump(title: str, payload: object) -> str:
    if not payload:
        return f"{title}: нет данных в текущем тарифе/эндпоинте."
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if len(text) > 3800:
        text = text[:3800] + "\n..."
    return f"{title}:\n<pre>{text}</pre>"

