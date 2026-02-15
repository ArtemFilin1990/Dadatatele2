from __future__ import annotations

from dataclasses import dataclass

import aiohttp


DADATA_PARTY_BY_ID_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"


@dataclass(frozen=True)
class DaDataResult:
    inn: str
    name: str
    kpp: str | None
    ogrn: str | None
    address: str | None
    source: str


class DaDataDirectClient:
    def __init__(self, token: str, secret: str | None = None, timeout_seconds: float = 10.0) -> None:
        self._token = token
        self._secret = secret
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async def find_party_by_inn(self, inn: str) -> DaDataResult | None:
        headers = {
            "Authorization": f"Token {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._secret:
            headers["X-Secret"] = self._secret

        payload = {"query": inn}

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(DADATA_PARTY_BY_ID_URL, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        suggestions = data.get("suggestions") or []
        if not suggestions:
            return None

        first = suggestions[0]
        item_data = first.get("data") or {}
        return DaDataResult(
            inn=inn,
            name=first.get("value") or item_data.get("name", {}).get("full_with_opf") or "—",
            kpp=item_data.get("kpp"),
            ogrn=item_data.get("ogrn"),
            address=(item_data.get("address") or {}).get("unrestricted_value"),
            source="direct",
        )
