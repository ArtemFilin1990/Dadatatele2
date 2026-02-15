import asyncio

from src.clients.checko import CheckoClient
from src.clients.dadata import DaDataClient
from src.services.aggregator import AggregatorService
from src.services.reference_data import ReferenceDataService


class DummyCache:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ttl=None):
        self.data[key] = value


class DummyRefs(ReferenceDataService):
    def __init__(self):
        pass

    def okved_name(self, code: str) -> str:
        return "расшифровка не найдена"


class WeirdChecko:
    async def fetch_subject(self, inn):
        return "company", {"data": {"НаимСокр": None, "Контакты": {"Тел": "abc"}}}

    async def fetch_finances(self, inn):
        return None

    async def fetch_legal_cases(self, inn):
        return None

    async def fetch_enforcements(self, inn):
        return None

    async def fetch_inspections(self, inn):
        return None

    async def fetch_contracts(self, inn):
        return None


class WeirdDaData:
    async def fetch_party(self, inn):
        return {"data": {"phones": [{"value": "8(999)123-45-67"}], "emails": [{"value": "X@Y.RU"}]}}


def test_aggregator_graceful_with_weird_payloads():
    ag = AggregatorService(checko=WeirdChecko(), dadata=WeirdDaData(), refs=DummyRefs())
    profile, raw = asyncio.run(ag.build_profile("3525405517"))

    assert profile is not None
    assert profile.inn == "3525405517"
    assert "+79991234567" in profile.contacts
    assert "x@y.ru" in profile.contacts
    assert isinstance(raw, dict)


class StubChecko(CheckoClient):
    def __init__(self):
        super().__init__(api_key="k", cache=DummyCache())

    async def _request_with_retries(self, path, params):
        return {"items": []}


class StubDaData(DaDataClient):
    def __init__(self):
        super().__init__(api_key="k", secret="", cache=DummyCache())

    async def _request_with_retries(self, url, body, headers):
        return {"unexpected": "shape"}


def test_clients_graceful_on_unexpected_shapes():
    checko = StubChecko()
    dadata = StubDaData()

    entity, payload = asyncio.run(checko.fetch_subject("123456789012"))
    assert entity in {"entrepreneur", "person"}
    assert isinstance(payload, dict) or payload is None

    suggestion = asyncio.run(dadata.fetch_party("3525405517"))
    assert suggestion is None
