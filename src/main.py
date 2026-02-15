from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import configure_handlers, router
from src.clients.checko import CheckoClient
from src.clients.dadata import DaDataClient
from src.services.aggregator import AggregatorService
from src.services.cache import SQLiteTTLCache
from src.services.reference_data import ReferenceDataService
from src.services.settings import get_settings
from src.storage.session_store import SessionStore


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    cache = SQLiteTTLCache(db_path=settings.cache_db_path, default_ttl=settings.cache_ttl_seconds)
    refs = ReferenceDataService(db_path=settings.reference_db_path)
    checko = CheckoClient(settings.checko_api_key, cache)
    dadata = DaDataClient(settings.dadata_api_key, settings.dadata_secret, cache)
    aggregator = AggregatorService(checko=checko, dadata=dadata, refs=refs)

    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    sessions = SessionStore(ttl_seconds=settings.cache_ttl_seconds)
    configure_handlers(settings=settings, aggregator=aggregator, sessions=sessions)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
