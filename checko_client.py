"""Async client for Checko API with simple TTL cache."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

import aiohttp

from config import CHECKO_API_KEY, CHECKO_BASE_URL, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    expires_at: float
    value: dict[str, Any] | None


class TTLCache:
    def __init__(self) -> None:
        self._data: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> dict[str, Any] | None:
        async with self._lock:
            entry = self._data.get(key)
            if not entry:
                return None
            if entry.expires_at < time.time():
                self._data.pop(key, None)
                return None
            return entry.value

    async def set(self, key: str, value: dict[str, Any] | None, ttl_seconds: int) -> None:
        async with self._lock:
            self._data[key] = CacheEntry(expires_at=time.time() + ttl_seconds, value=value)


class CheckoClient:
    def __init__(self) -> None:
        self.enabled = bool(CHECKO_API_KEY)
        self.base_url = CHECKO_BASE_URL.rstrip("/")
        self.cache = TTLCache()

    async def _request(self, path: str, params: dict[str, str], ttl_seconds: int) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        cache_key = f"{path}:{sorted(params.items())}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}{path}"
        query = {"key": CHECKO_API_KEY, **params}
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)) as session:
                async with session.get(url, params=query) as resp:
                    if resp.status != 200:
                        logger.warning("Checko HTTP %s for %s", resp.status, path)
                        return None
                    data = await resp.json()
                    await self.cache.set(cache_key, data, ttl_seconds=ttl_seconds)
                    return data
        except Exception:
            logger.exception("Checko request failed for %s", path)
            return None

    async def fetch_subject(self, inn: str) -> tuple[str | None, dict[str, Any] | None]:
        if len(inn) == 10:
            payload = await self._request("/v2/company", {"inn": inn}, ttl_seconds=86400)
            return "company", payload

        if len(inn) == 12:
            payload = await self._request("/v2/entrepreneur", {"inn": inn}, ttl_seconds=86400)
            if self._has_result(payload):
                return "entrepreneur", payload
            payload = await self._request("/v2/person", {"inn": inn}, ttl_seconds=86400)
            return "person", payload

        return None, None

    async def fetch_finances(self, inn: str) -> dict[str, Any] | None:
        return await self._request("/v2/finances", {"inn": inn}, ttl_seconds=7 * 86400)

    async def fetch_legal_cases(self, inn: str) -> dict[str, Any] | None:
        return await self._request("/v2/legal-cases", {"inn": inn}, ttl_seconds=86400)

    async def fetch_enforcements(self, inn: str) -> dict[str, Any] | None:
        return await self._request("/v2/enforcements", {"inn": inn}, ttl_seconds=12 * 3600)

    async def fetch_inspections(self, inn: str) -> dict[str, Any] | None:
        return await self._request("/v2/inspections", {"inn": inn}, ttl_seconds=7 * 86400)

    async def fetch_contracts(self, inn: str) -> dict[str, Any] | None:
        return await self._request("/v2/contracts", {"inn": inn}, ttl_seconds=86400)

    @staticmethod
    def _has_result(payload: dict[str, Any] | None) -> bool:
        if not payload:
            return False
        if payload.get("data"):
            return True
        return bool(payload.get("items"))


checko_client = CheckoClient()
