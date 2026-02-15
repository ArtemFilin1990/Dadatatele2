from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheItem:
    expires_at: float
    value: Any


class TTLCache:
    def __init__(self, default_ttl: int) -> None:
        self.default_ttl = default_ttl
        self._data: dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            if item.expires_at <= time.time():
                self._data.pop(key, None)
                return None
            return item.value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        async with self._lock:
            self._data[key] = CacheItem(expires_at=time.time() + ttl_seconds, value=value)
