from __future__ import annotations

from dataclasses import replace

from dadata_direct import DaDataDirectClient, DaDataResult


class DaDataMCPClient:
    """
    MCP-заглушка: интерфейс сохранён, но используется прямой DaData-клиент.

    Это безопасный обратимый вариант до подключения подтверждённой MCP-конфигурации
    и transport-слоя в конкретном окружении.
    """

    def __init__(self, fallback_client: DaDataDirectClient) -> None:
        self._fallback_client = fallback_client

    async def find_party_by_inn(self, inn: str) -> DaDataResult | None:
        result = await self._fallback_client.find_party_by_inn(inn)
        if result is None:
            return None
        return replace(result, source="mcp-fallback")
