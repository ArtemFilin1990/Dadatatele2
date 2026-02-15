"""Unified enrichment layer: Checko truth + DaData contacts/tips."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from checko_client import checko_client
from dadata_direct import fetch_company


@dataclass
class CompanyProfile:
    inn: str
    entity_type: str
    name: str
    ogrn: str
    kpp: str
    status: str
    address: str
    okved: str
    contacts: list[str]
    risk_label: str
    risk_notes: list[str]
    source_notes: list[str]


def _pick(data: dict[str, Any], *keys: str, default: str = "—") -> str:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits
    return raw.strip()


def _dedup_contacts(checko_contacts: list[str], dadata_contacts: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    def add(value: str) -> None:
        key = value.lower().strip()
        if key in seen:
            return
        seen.add(key)
        result.append(value)

    for item in checko_contacts + dadata_contacts:
        add(item)
    return result


def _risk_score(raw: dict[str, Any]) -> tuple[str, list[str]]:
    notes: list[str] = []

    status = str(raw.get("status") or raw.get("Статус") or "").lower()
    if any(s in status for s in ["ликвид", "прекращ", "liquid"]):
        notes.append("Статус указывает на ликвидацию/прекращение деятельности")

    for key, note in [
        ("Санкции", "Есть флаг санкций"),
        ("НелегалФин", "Есть флаг нелегальной финансовой деятельности"),
        ("ДисквЛица", "Есть дисквалифицированные лица"),
        ("МассРуковод", "Признак массового руководителя"),
        ("МассУчред", "Признак массового учредителя"),
    ]:
        if raw.get(key) is True:
            notes.append(note)

    if any("ликвидац" in n.lower() or "санкц" in n.lower() for n in notes):
        return "🟥 Высокий риск", notes
    if notes:
        return "🟧 Средний риск", notes
    return "🟩 Низкий риск", notes


def _extract_checko_contacts(raw: dict[str, Any]) -> list[str]:
    contacts = raw.get("Контакты") or raw.get("contacts") or {}
    values: list[str] = []
    for key in ("Тел", "phone", "phones"):
        val = contacts.get(key)
        if isinstance(val, list):
            for p in val:
                values.append(_normalize_phone(str(p)))
        elif val:
            values.append(_normalize_phone(str(val)))

    for key in ("Емэйл", "Email", "email", "emails"):
        val = contacts.get(key)
        if isinstance(val, list):
            for em in val:
                values.append(str(em).strip().lower())
        elif val:
            values.append(str(val).strip().lower())

    site = contacts.get("ВебСайт") or contacts.get("site")
    if site:
        values.append(str(site).strip())
    return [v for v in values if v and v != "—"]


def _extract_dadata_contacts(suggestion: dict[str, Any] | None) -> list[str]:
    if not suggestion:
        return []
    data = suggestion.get("data", {})
    values: list[str] = []
    for phone in data.get("phones") or []:
        if phone.get("value"):
            values.append(_normalize_phone(phone["value"]))
    for email in data.get("emails") or []:
        if email.get("value"):
            values.append(email["value"].strip().lower())
    return values


async def build_profile(inn: str) -> CompanyProfile | None:
    source_notes: list[str] = []
    entity, payload = await checko_client.fetch_subject(inn)

    checko_raw: dict[str, Any] = {}
    if payload and isinstance(payload, dict):
        checko_raw = payload.get("data") or payload.get("company") or payload.get("entrepreneur") or payload

    dadata_item = await fetch_company(inn)

    if not checko_raw and not dadata_item:
        return None

    if not checko_raw:
        source_notes.append("Checko недоступен: карточка собрана без ЕГРЮЛ/рисков")

    dadata_data = (dadata_item or {}).get("data", {})

    name = _pick(
        checko_raw,
        "НаимПолн",
        "name",
        default=str(dadata_data.get("name", {}).get("short_with_opf") or "—"),
    )
    profile = CompanyProfile(
        inn=inn,
        entity_type=entity or ("company" if len(inn) == 10 else "entrepreneur/person"),
        name=name,
        ogrn=_pick(checko_raw, "ОГРН", "ogrn", default=str(dadata_data.get("ogrn") or "—")),
        kpp=_pick(checko_raw, "КПП", "kpp", default=str(dadata_data.get("kpp") or "—")),
        status=_pick(checko_raw, "Статус", "status", default="—"),
        address=_pick(
            checko_raw,
            "ЮрАдрес",
            "address",
            default=str((dadata_data.get("address") or {}).get("unrestricted_value") or "—"),
        ),
        okved=_pick(checko_raw, "ОКВЭД", "okved", default=str(dadata_data.get("okved") or "—")),
        contacts=_dedup_contacts(_extract_checko_contacts(checko_raw), _extract_dadata_contacts(dadata_item)),
        risk_label="",
        risk_notes=[],
        source_notes=source_notes,
    )
    profile.risk_label, profile.risk_notes = _risk_score(checko_raw)
    return profile


def render_summary(profile: CompanyProfile) -> str:
    contacts = "\n".join(f"• {c}" for c in profile.contacts[:5]) if profile.contacts else "—"
    notes = "\n".join(f"• {n}" for n in profile.source_notes) if profile.source_notes else "—"
    risk_notes = "\n".join(f"• {n}" for n in profile.risk_notes[:5]) if profile.risk_notes else "—"
    return (
        f"<b>📋 {profile.name}</b>\n"
        f"ИНН: <code>{profile.inn}</code>\n"
        f"ОГРН: <code>{profile.ogrn}</code>\n"
        f"КПП: <code>{profile.kpp}</code>\n"
        f"Статус: {profile.status}\n"
        f"ОКВЭД: {profile.okved}\n"
        f"Адрес: {profile.address}\n\n"
        f"<b>Риск:</b> {profile.risk_label}\n{risk_notes}\n\n"
        f"<b>Контакты:</b>\n{contacts}\n\n"
        f"<b>Источник:</b>\n{notes}"
    )


def render_section(title: str, payload: dict[str, Any] | None) -> str:
    if not payload:
        return f"<b>{title}</b>\nДанные временно недоступны."
    text = str(payload)
    if len(text) > 3500:
        text = text[:3500] + "\n..."
    return f"<b>{title}</b>\n<code>{text}</code>"
