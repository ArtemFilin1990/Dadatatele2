"""Конфигурация бота: загрузка и валидация переменных окружения."""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _first_non_empty(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""


TELEGRAM_BOT_TOKEN: str = _first_non_empty("TELEGRAM_BOT_TOKEN")
DADATA_API_KEY: str = _first_non_empty("DADATA_API_KEY", "DADATA_API_TOKEN")
DADATA_SECRET_KEY: str = _first_non_empty("DADATA_SECRET_KEY", "DADATA_API_SECRET")
OPENAI_API_KEY: str = _first_non_empty("OPENAI_API_KEY")
CHECKO_API_KEY: str = _first_non_empty("CHECKO_API_KEY")
CHECKO_BASE_URL: str = _first_non_empty("CHECKO_BASE_URL") or "https://api.checko.ru"
OPENAI_MODEL: str = _first_non_empty("OPENAI_MODEL") or "gpt-4.1-mini"
LOG_LEVEL: str = _first_non_empty("LOG_LEVEL") or "INFO"

BOT_MODE: str = (_first_non_empty("BOT_MODE") or "polling").lower()
WEBHOOK_BASE_URL: str = _first_non_empty("WEBHOOK_BASE_URL")
WEBHOOK_PATH: str = _first_non_empty("WEBHOOK_PATH") or "/webhook"
WEBHOOK_SECRET_TOKEN: str = _first_non_empty("WEBHOOK_SECRET_TOKEN")
WEB_SERVER_HOST: str = _first_non_empty("WEB_SERVER_HOST") or "0.0.0.0"
WEB_SERVER_PORT_RAW: str = _first_non_empty("WEB_SERVER_PORT") or "8080"

_timeout_raw = _first_non_empty("REQUEST_TIMEOUT_SECONDS") or "15"
try:
    REQUEST_TIMEOUT_SECONDS = float(_timeout_raw)
    if REQUEST_TIMEOUT_SECONDS <= 0:
        raise ValueError
except ValueError:
    logging.error("REQUEST_TIMEOUT_SECONDS должен быть положительным числом, получено: %s", _timeout_raw)
    sys.exit(1)

try:
    WEB_SERVER_PORT = int(WEB_SERVER_PORT_RAW)
    if not (1 <= WEB_SERVER_PORT <= 65535):
        raise ValueError
except ValueError:
    logging.error("WEB_SERVER_PORT должен быть целым числом от 1 до 65535, получено: %s", WEB_SERVER_PORT_RAW)
    sys.exit(1)

_required = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "DADATA_API_KEY (или DADATA_API_TOKEN)": DADATA_API_KEY,
}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    logging.error("Не заданы переменные окружения: %s", ", ".join(_missing))
    sys.exit(1)

if BOT_MODE not in {"polling", "webhook"}:
    logging.error("BOT_MODE должен быть polling или webhook, получено: %s", BOT_MODE)
    sys.exit(1)

if BOT_MODE == "webhook" and not WEBHOOK_BASE_URL:
    logging.error("Для BOT_MODE=webhook требуется WEBHOOK_BASE_URL")
    sys.exit(1)

if not WEBHOOK_PATH.startswith("/"):
    logging.error("WEBHOOK_PATH должен начинаться с '/', получено: %s", WEBHOOK_PATH)
    sys.exit(1)

DADATA_FIND_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
OPENAI_BASE_URL = "https://api.openai.com/v1"
MCP_SERVER_URL = "https://mcp.dadata.ru/mcp"
