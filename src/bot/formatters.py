from __future__ import annotations

from src.services.aggregator import Profile


def format_card(profile: Profile) -> str:
    status_icon = "❌" if "ликвид" in profile.status.lower() or "прекращ" in profile.status.lower() else "✅"
    contacts = " • ".join(profile.contacts[:3]) if profile.contacts else "—"
    liquidation = (
        f"\n⚠️ Ликвидировано {profile.liquidation_date} — для договоров/оплат аккуратно."
        if profile.liquidation_date
        else ""
    )
    successor = f"\n✅ Правопреемник: {profile.successor}" if profile.successor else ""
    conflict = "\n⚠️ Источники расходятся: проверьте детали в разделах." if profile.source_dispute else ""

    return (
        "Готово ✅\n"
        f"🏢 {profile.short_name} (полное: {profile.full_name})\n"
        f"📅 Регистрация: {profile.registration_date}\n"
        f"🆔 ИНН/КПП: {profile.inn}/{profile.kpp}\n"
        f"🧾 ОГРН: {profile.ogrn}\n"
        f"💰 Уставный капитал: {profile.capital}\n"
        f"👤 Руководитель: {profile.manager}\n"
        f"{status_icon} Статус: {profile.status}"
        f"{liquidation}"
        f"{successor}\n"
        f"📍 Адрес: {profile.address}\n"
        f"🏷️ ОКВЭД: {profile.okved} — {profile.okved_title}\n"
        f"📞/✉️/🌐: {contacts}"
        f"{conflict}"
    )
