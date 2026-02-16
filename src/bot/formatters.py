from __future__ import annotations

from html import escape

from src.services.aggregator import Profile


def format_card(profile: Profile) -> str:
    status_icon = "❌" if "ликвид" in profile.status.lower() or "прекращ" in profile.status.lower() else "✅"
    contacts = " • ".join(escape(value) for value in profile.contacts[:3]) if profile.contacts else "—"
    liquidation = (
        f"\n⚠️ Ликвидировано {escape(profile.liquidation_date)} — для договоров/оплат аккуратно."
        if profile.liquidation_date
        else ""
    )
    successor = f"\n✅ Правопреемник: {escape(profile.successor)}" if profile.successor else ""
    conflict = "\n⚠️ Источники расходятся: проверьте детали в разделах." if profile.source_dispute else ""

    return (
        "Готово ✅\n"
        f"🏢 {escape(profile.short_name)} (полное: {escape(profile.full_name)})\n"
        f"📅 Регистрация: {escape(profile.registration_date)}\n"
        f"🆔 ИНН/КПП: {escape(profile.inn)}/{escape(profile.kpp)}\n"
        f"🧾 ОГРН: {escape(profile.ogrn)}\n"
        f"💰 Уставный капитал: {escape(profile.capital)}\n"
        f"👤 Руководитель: {escape(profile.manager)}\n"
        f"{status_icon} Статус: {escape(profile.status)}"
        f"{liquidation}"
        f"{successor}\n"
        f"📍 Адрес: {escape(profile.address)}\n"
        f"🏷️ ОКВЭД: {escape(profile.okved)} — {escape(profile.okved_title)}\n"
        f"📞/✉️/🌐: {contacts}"
        f"{conflict}"
    )
