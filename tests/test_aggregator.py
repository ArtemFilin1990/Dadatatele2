import asyncio

from src.services.aggregator import AggregatorService


class _CheckoStub:
    def __init__(self, payload):
        self.payload = payload

    async def fetch_subject(self, inn: str):
        return "company", self.payload


class _DaDataStub:
    def __init__(self, payload):
        self.payload = payload

    async def fetch_party(self, inn: str):
        return self.payload


def test_build_profile_returns_none_without_dadata():
    service = AggregatorService(
        checko=_CheckoStub({"data": {"НаимСокр": 'ООО "Тест"'}}),
        dadata=_DaDataStub(None),
    )

    profile, _ = asyncio.run(service.build_profile("3525405517"))

    assert profile is None


def test_build_profile_uses_dadata_when_checko_empty():
    service = AggregatorService(
        checko=_CheckoStub(None),
        dadata=_DaDataStub(
            {
                "data": {
                    "name": {
                        "short_with_opf": 'ООО "Ромашка"',
                        "full_with_opf": 'Общество с ограниченной ответственностью "Ромашка"',
                    },
                    "kpp": "123456789",
                    "ogrn": "1234567890123",
                }
            }
        ),
    )

    profile, _ = asyncio.run(service.build_profile("3525405517"))

    assert profile is not None
    assert profile.short_name == 'ООО "Ромашка"'
