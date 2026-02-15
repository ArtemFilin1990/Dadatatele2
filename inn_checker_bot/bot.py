from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import AppConfig
from dadata_direct import DaDataDirectClient
from dadata_mcp import DaDataMCPClient
from handlers import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = AppConfig.from_env()
    bot = Bot(
        token=config.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    direct_client = DaDataDirectClient(
        token=config.dadata_token,
        secret=config.dadata_secret,
        timeout_seconds=config.request_timeout_seconds,
    )
    mcp_client = DaDataMCPClient(fallback_client=direct_client)

    dp["direct_client"] = direct_client
    dp["mcp_client"] = mcp_client
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
