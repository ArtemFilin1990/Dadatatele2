from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from src.services.cache import SQLiteTTLCache

logger = logging.getLogger(__name__)


class DaDataClient:
    URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"

    def __init__(self, api_key: str, secret: str, cache: SQLiteTTLCache) -> None:
        self.api_key = api_key
        self.secret = secret
        self.cache = cache

    async def fetch_party(self, inn: str) -> dict[str, Any] | None:
        cache_key = f"dadata|findById/party|{inn}|query={inn}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
        }
        if self.secret:
            headers["X-Secret"] = self.secret

        data = await self._request_with_retries(self.URL, {"query": inn}, headers)
        if not data:
            return None
        suggestions = data.get("suggestions") or []
        result = suggestions[0] if suggestions else None
        await self.cache.set(cache_key, result)
        return result

    async def _request_with_retries(self, url: str, body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any] | None:
        timeout = aiohttp.ClientTimeout(total=15)
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=body, headers=headers) as resp:
                        if resp.status == 429 or 500 <= resp.status < 600:
                            raise aiohttp.ClientResponseError(
                                request_info=resp.request_info,
                                history=resp.history,
                                status=resp.status,
                            )
                        if resp.status != 200:
                            logger.warning("DaData HTTP %s for INN %s", resp.status, body.get("query"))
                            return None
                        return await resp.json()
            except Exception:
                if attempt == 2:
                    logger.exception("DaData request failed for INN %s", body.get("query"))
                    return None
                await asyncio.sleep(0.7 * (attempt + 1))
        return None
