from src.clients.checko import CheckoClient
from src.clients.dadata import DaDataClient
from src.services.aggregator import AggregatorService
from src.services.reference_data import ReferenceDataService


class DummyChecko(CheckoClient):
    def __init__(self):
        pass

    async def fetch_subject(self, inn):
        return "company", {
            "data": {
                "НаимСокр": "ООО Ромашка",
                "ЮрАдрес": "Москва",
                "Статус": "ACTIVE",
                "ОКВЭД": "62.01",
                "Контакты": {"Тел": ["8 (999) 000-11-22"], "Емэйл": ["A@B.ru"]},
            }
        }


class DummyDaData(DaDataClient):
    def __init__(self):
        pass

    async def fetch_party(self, inn):
        return {
            "data": {
                "name": {"short_with_opf": "ООО РОМАШКА"},
                "phones": [{"value": "+7 999 000 11 22"}],
                "emails": [{"value": "a@b.ru"}],
                "address": {"unrestricted_value": "Москва"},
                "state": {"status": "ACTIVE"},
            }
        }


class DummyRefs(ReferenceDataService):
    def __init__(self):
        pass

    def okved_name(self, code: str) -> str:
        return "Разработка ПО"


def test_merge_contacts_and_conflict_flag():
    ag = AggregatorService(checko=DummyChecko(), dadata=DummyDaData(), refs=DummyRefs())
    import asyncio

    profile, _ = asyncio.run(ag.build_profile("3525405517"))
    assert profile is not None
    assert "+79990001122" in profile.contacts
    assert "a@b.ru" in profile.contacts
    assert profile.source_dispute is True
