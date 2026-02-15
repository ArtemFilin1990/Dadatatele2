from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    telegram_bot_token: str
    dadata_token: str
    dadata_secret: str | None
    openai_api_key: str | None
    openai_model: str
    request_timeout_seconds: float

    @staticmethod
    def from_env() -> "AppConfig":
        load_dotenv()

        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        dadata_token = os.getenv("DADATA_API_TOKEN", "").strip()
        dadata_secret = os.getenv("DADATA_API_SECRET", "").strip() or None
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip() or None
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
        timeout_raw = os.getenv("REQUEST_TIMEOUT_SECONDS", "10").strip()

        if not telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not dadata_token:
            raise ValueError("DADATA_API_TOKEN is required")

        try:
            request_timeout_seconds = float(timeout_raw)
            if request_timeout_seconds <= 0:
                raise ValueError
        except ValueError as exc:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be a positive number") from exc

        return AppConfig(
            telegram_bot_token=telegram_bot_token,
            dadata_token=dadata_token,
            dadata_secret=dadata_secret,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            request_timeout_seconds=request_timeout_seconds,
        )
