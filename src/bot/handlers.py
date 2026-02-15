from __future__ import annotations

import io
import json
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.formatters import format_card
from src.bot.keyboards import CB, card_inline_kb, start_kb, subpage_kb
from src.bot.states import MainState
from src.services.aggregator import AggregatorService
from src.services.inn import validate_inn
from src.services.settings import Settings
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


@router.callback_query(F.data == CB["back"])
async def nav_back(callback: CallbackQuery) -> None:
    if _sessions is None or _aggregator is None:
        await callback.answer("Сервис не инициализирован")
        return
    session = _sessions.get(callback.from_user.id)
    if not session.stack:
        await callback.answer("Сначала проверьте ИНН")
        return
    if len(session.stack) > 1:
        session.stack.pop()
    _sessions.save(callback.from_user.id, session)
    await callback.message.edit_text(session.stack[-1], reply_markup=card_inline_kb())
    await callback.answer()


@router.callback_query(F.data == CB["home"])
async def nav_home(callback: CallbackQuery) -> None:
    if _sessions is None:
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
async def page_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if _aggregator is None:
        await callback.answer("Сервис не инициализирован")
        return
    if not callback.data:
        await callback.answer("Раздел недоступен")
        return

    page = callback.data.split(":", 1)[1]
    if _sessions is None:
        await callback.answer("Сервис не инициализирован")
        return
    session = _sessions.get(callback.from_user.id)
    if not session.current_inn:
        await callback.answer("Сначала проверьте ИНН")
        return

    checko = _aggregator.checko
    inn = session.current_inn

    if page == "new_inn":
        await state.set_state(MainState.waiting_inn)
        await callback.message.edit_text("Введите новый ИНН (10 или 12 цифр).", reply_markup=subpage_kb())
        await callback.answer()
        return

    if page == "menu":
        await callback.message.edit_text("Главное меню обновлено.", reply_markup=subpage_kb())
        await callback.message.answer("Выберите действие в меню ниже.", reply_markup=start_kb())
        await callback.answer()
        return

    checko_data = _extract_checko_data(session.extra)

    if page == "successor":
        text = f"Правопреемник: {checko_data.get('Правопреемник', 'нет данных')}"
    elif page == "contacts":
        text = "Все контакты из карточки и источников уже собраны в основном экране."
    elif page == "authorities":
        text = "ФНС/ПФР/ФСС/Росстат: данные зависят от ответа Checko и тарифа."
    elif page == "finance":
        text = _dump("Финансы", await checko.fetch_finance(inn))
    elif page == "cases":
        text = _dump("Суды", await checko.fetch_legal_cases(inn))
    elif page == "founders":
        text = _dump("Учредители", checko_data.get("Учред"))
    elif page == "contracts":
        text = _dump("Госзакупки", await checko.fetch_contracts(inn))
    elif page == "taxes":
        text = _dump("Налоги", checko_data.get("Налоги"))
    elif page == "debts":
        text = _dump("Долги", await checko.fetch_enforcements(inn))
    elif page == "inspections":
        text = _dump("Проверки", await checko.fetch_inspections(inn))
    else:
        text = "Раздел недоступен."

    session.stack.append(text)
    _sessions.save(callback.from_user.id, session)
    await callback.message.edit_text(text, reply_markup=subpage_kb())
    await callback.answer()


@router.message()
async def fallback_message(message: Message, state: FSMContext) -> None:
    await state.set_state(MainState.waiting_inn)
    await message.answer("Не понял запрос. Нажмите «🔎 Проверить ИНН» или отправьте ИНН (10 или 12 цифр).")


@router.callback_query(F.data == CB["pdf"])
async def export_pdf(callback: CallbackQuery) -> None:
    if _sessions is None:
        await callback.answer("Сервис не инициализирован")
        return
    session = _sessions.get(callback.from_user.id)
    if not session.current_card:
        await callback.answer("Нет карточки для экспорта")
        return

    data = _make_pdf(session.current_card)
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


def _extract_checko_data(extra: dict[str, object]) -> dict[str, object]:
    payload = extra.get("checko")
    if not isinstance(payload, dict):
        return {}
    nested = payload.get("data")
    if isinstance(nested, dict):
        return nested
    return payload


def _make_pdf(text: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        stream = io.BytesIO()
        c = canvas.Canvas(stream, pagesize=A4)
        y = 800
        for line in text.splitlines():
            c.drawString(30, y, line[:110])
            y -= 14
            if y < 40:
                c.showPage()
                y = 800
        c.save()
        stream.seek(0)
        return stream.read()
    except Exception:
        return text.encode("utf-8")
