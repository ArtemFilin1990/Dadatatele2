from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    checko_api_key: str
    dadata_api_key: str
    dadata_secret: str
    cache_ttl_seconds: int
    strict_inn_check: bool
    log_level: str



def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    checko_key = os.getenv("CHECKO_API_KEY", "").strip()
    dadata_key = os.getenv("DADATA_API_KEY", "").strip()
    dadata_secret = os.getenv("DADATA_SECRET", "").strip()
    cache_ttl_raw = os.getenv("CACHE_TTL_SECONDS", "21600").strip()
    strict_inn = _as_bool(os.getenv("STRICT_INN_CHECK", "false"))
    log_level = os.getenv("LOG_LEVEL", "INFO").strip() or "INFO"

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    if not checko_key:
        raise ValueError("CHECKO_API_KEY is required")
    if not dadata_key:
        raise ValueError("DADATA_API_KEY is required")

    try:
        cache_ttl = int(cache_ttl_raw)
        if cache_ttl <= 0:
            raise ValueError
    except ValueError as exc:
        raise ValueError("CACHE_TTL_SECONDS must be positive integer") from exc

    return Settings(
        telegram_bot_token=token,
        checko_api_key=checko_key,
        dadata_api_key=dadata_key,
        dadata_secret=dadata_secret,
        cache_ttl_seconds=cache_ttl,
        strict_inn_check=strict_inn,
        log_level=log_level,
    )
