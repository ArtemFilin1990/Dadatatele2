from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlencode

import aiohttp

from src.services.cache import SQLiteTTLCache

logger = logging.getLogger(__name__)


class CheckoClient:
    BASE_URL = "https://api.checko.ru"

    def __init__(self, api_key: str, cache: SQLiteTTLCache) -> None:
        self.api_key = api_key
        self.cache = cache

    async def fetch_subject(self, inn: str) -> tuple[str | None, dict[str, Any] | None]:
        if len(inn) == 10:
            return "company", await self._call("/v2/company", {"inn": inn}, ttl=86400)
        if len(inn) == 12:
            ent = await self._call("/v2/entrepreneur", {"inn": inn}, ttl=86400)
            if self._has_data(ent):
                return "entrepreneur", ent
            person = await self._call("/v2/person", {"inn": inn}, ttl=86400)
            return "person", person
        return None, None

    async def fetch_finances(self, inn: str) -> dict[str, Any] | None:
        return await self._call("/v2/finances", {"inn": inn}, ttl=7 * 86400)

    async def fetch_contracts(self, inn: str) -> dict[str, Any] | None:
        return await self._call("/v2/contracts", {"inn": inn}, ttl=86400)

    async def fetch_enforcements(self, inn: str) -> dict[str, Any] | None:
        return await self._call("/v2/enforcements", {"inn": inn, "limit": "5", "sort": "-date"}, ttl=43200)

    async def fetch_inspections(self, inn: str) -> dict[str, Any] | None:
        return await self._call("/v2/inspections", {"inn": inn, "limit": "5", "sort": "-date"}, ttl=7 * 86400)

    async def fetch_legal_cases(self, inn: str) -> dict[str, Any] | None:
        params = {"inn": inn, "limit": "5", "sort": "-date", "actual": "true"}
        return await self._call("/v2/legal-cases", params, ttl=86400)

    async def _call(self, path: str, params: dict[str, str], ttl: int) -> dict[str, Any] | None:
        query = {"key": self.api_key, **params}
        cache_key = f"checko|{path}|{params.get('inn','')}|{urlencode(sorted(params.items()))}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        data = await self._request_with_retries(path, query)
        if data is not None:
            await self.cache.set(cache_key, data, ttl=ttl)
        return data

    async def _request_with_retries(self, path: str, params: dict[str, str]) -> dict[str, Any] | None:
        timeout = aiohttp.ClientTimeout(total=15)
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(f"{self.BASE_URL}{path}", params=params) as resp:
                        if resp.status == 429 or 500 <= resp.status < 600:
                            raise aiohttp.ClientResponseError(
                                request_info=resp.request_info,
                                history=resp.history,
                                status=resp.status,
                            )
                        if resp.status != 200:
                            logger.warning("Checko HTTP %s for %s", resp.status, path)
                            return None
                        return await resp.json()
            except Exception:
                if attempt == 2:
                    logger.exception("Checko request failed for %s", path)
                    return None
                await asyncio.sleep(0.7 * (attempt + 1))

        return None

    @staticmethod
    def _has_data(payload: dict[str, Any] | None) -> bool:
        if not payload:
            return False
        return bool(payload.get("data") or payload.get("items"))
