from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from src.clients.checko import CheckoClient
from src.clients.dadata import DaDataClient
from src.services.reference_data import decode_okved


@dataclass
class Profile:
    inn: str
    short_name: str
    full_name: str
    ogrn: str
    kpp: str
    status: str
    registration_date: str
    liquidation_date: str
    address: str
    manager: str
    capital: str
    okved: str
    okved_title: str
    contacts: list[str]
    successor: str
    source_dispute: bool


def _as_str(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _norm_phone(text: str) -> str:
    digits = re.sub(r"\D", "", text)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) == 11 and digits.startswith("7"):
        return f"+{digits}"
    return text.strip()


class AggregatorService:
    def __init__(self, checko: CheckoClient, dadata: DaDataClient) -> None:
        self.checko = checko
        self.dadata = dadata

    async def build_profile(self, inn: str) -> tuple[Profile | None, dict[str, Any]]:
        entity, checko_payload = await self.checko.fetch_subject(inn)
        dadata_payload = await self.dadata.fetch_party(inn)

        checko_data = (checko_payload or {}).get("data") or (checko_payload or {})
        dadata_data = (dadata_payload or {}).get("data") or {}

        if not dadata_payload:
            return None, {"entity": entity}

        checko_name = _as_str(checko_data.get("НаимСокр") or checko_data.get("name"), "")
        dadata_name = _as_str((dadata_data.get("name") or {}).get("short_with_opf"), "")
        source_dispute = bool(checko_name and dadata_name and checko_name != dadata_name)

        contacts = self._merge_contacts(checko_data, dadata_data)
        okved_code = _as_str(checko_data.get("ОКВЭД") or dadata_data.get("okved"))
        profile = Profile(
            inn=inn,
            short_name=checko_name or dadata_name or "—",
            full_name=_as_str(checko_data.get("НаимПолн") or (dadata_data.get("name") or {}).get("full_with_opf")),
            ogrn=_as_str(checko_data.get("ОГРН") or dadata_data.get("ogrn")),
            kpp=_as_str(checko_data.get("КПП") or dadata_data.get("kpp")),
            status=_as_str(checko_data.get("Статус") or (dadata_data.get("state") or {}).get("status")),
            registration_date=_as_str(checko_data.get("ДатаРег") or (dadata_data.get("state") or {}).get("registration_date")),
            liquidation_date=_as_str(checko_data.get("ДатаПрекр") or (dadata_data.get("state") or {}).get("liquidation_date"), ""),
            address=_as_str(checko_data.get("ЮрАдрес") or (dadata_data.get("address") or {}).get("unrestricted_value")),
            manager=_as_str((checko_data.get("Руковод") or {}).get("ФИО") or (dadata_data.get("management") or {}).get("name")),
            capital=_as_str((checko_data.get("Капитал") or {}).get("Сумма") or (dadata_data.get("capital") or {}).get("value")),
            okved=okved_code,
            okved_title=decode_okved(okved_code),
            contacts=contacts,
            successor=_as_str(checko_data.get("Правопреемник") or "", ""),
            source_dispute=source_dispute,
        )
        return profile, {"entity": entity, "checko": checko_payload}

    @staticmethod
    def _merge_contacts(checko_data: dict[str, Any], dadata_data: dict[str, Any]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()

        contacts = checko_data.get("Контакты") or {}
        for raw in contacts.get("Тел", []) if isinstance(contacts.get("Тел"), list) else [contacts.get("Тел")]:
            if raw:
                val = _norm_phone(str(raw))
                if val.lower() not in seen:
                    seen.add(val.lower())
                    out.append(val)

        for phone in dadata_data.get("phones") or []:
            raw = phone.get("value")
            if raw:
                val = _norm_phone(str(raw))
                if val.lower() not in seen:
                    seen.add(val.lower())
                    out.append(val)

        emails: list[str] = []
        for raw in contacts.get("Емэйл", []) if isinstance(contacts.get("Емэйл"), list) else [contacts.get("Емэйл")]:
            if raw:
                emails.append(str(raw).strip().lower())
        for email in dadata_data.get("emails") or []:
            if email.get("value"):
                emails.append(str(email["value"]).strip().lower())

        for email in emails:
            if email and email not in seen:
                seen.add(email)
                out.append(email)

        site = contacts.get("ВебСайт")
        if site:
            val = str(site).strip().lower()
            if val not in seen:
                seen.add(val)
                out.append(val)

        return out
