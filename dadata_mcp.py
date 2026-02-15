"""Запрос к DaData через MCP-сервер с использованием OpenAI Responses API."""

import logging

from openai import OpenAI

from config import (
    DADATA_API_KEY,
    DADATA_SECRET_KEY,
    MCP_SERVER_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    REQUEST_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


async def fetch_company_via_mcp(inn: str) -> str:
    """Проверка компании через DaData MCP + OpenAI AI."""
    if not DADATA_SECRET_KEY:
        return "❌ MCP-режим недоступен: не задан DADATA_SECRET_KEY (или DADATA_API_SECRET)."
    if not OPENAI_API_KEY:
        return "❌ MCP-режим недоступен: не задан OPENAI_API_KEY."

    try:
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response = client.responses.create(
            model=OPENAI_MODEL,
            tools=[
                {
                    "type": "mcp",
                    "server_label": "dadata",
                    "server_url": MCP_SERVER_URL,
                    "headers": {
                        "authorization": f"Bearer {DADATA_API_KEY}:{DADATA_SECRET_KEY}",
                    },
                    "require_approval": "never",
                }
            ],
            input=(
                f"Проверь контрагента по ИНН {inn}. Надёжный ли он? "
                "Дай подробный анализ: реквизиты, статус, адрес, руководство, финансы."
            ),
        )

        result_text = ""
        for item in response.output:
            if hasattr(item, "content"):
                for content_block in item.content:
                    if hasattr(content_block, "text"):
                        result_text += content_block.text

        return result_text or str(response.output)

    except Exception:
        logger.exception("MCP error for INN %s", inn)
        return "❌ Ошибка MCP-запроса. Попробуйте позже или используйте режим DaData напрямую."
