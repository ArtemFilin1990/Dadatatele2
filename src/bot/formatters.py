from __future__ import annotations

from src.services.aggregator import Profile


def format_card(profile: Profile) -> str:
    status_lower = profile.status.lower()
    status_icon = "❌" if "ликвид" in status_lower or "прекращ" in status_lower else "✅"
    contacts = " • ".join(profile.contacts[:3]) if profile.contacts else "—"
    liquidation = (
        f"\n⚠️ Ликвидировано {profile.liquidation_date} — для договоров/оплат аккуратно."
        if profile.liquidation_date
        else ""
    )
    successor = f"\n✅ Правопреемник: {profile.successor}" if profile.successor else ""
    conflict = "\n⚠️ Источники расходятся. Детали: " + profile.conflict_details if profile.source_dispute else ""

    return (
        "Готово ✅\n"
        f"🏢 {profile.short_name} (полное: {profile.full_name})\n"
        f"📅 Регистрация: {profile.registration_date}\n"
        f"🆔 ИНН/КПП: {profile.inn}/{profile.kpp}\n"
        f"🧾 ОГРН: {profile.ogrn}\n"
        f"💰 Уставный капитал: {profile.capital}\n"
        f"👤 гендир: {profile.manager}\n"
        f"👥 Штат: {profile.staff} • 💵 Ср. зарплата: {profile.avg_salary}\n"
        f"{status_icon} Статус: {profile.status}"
        f"{liquidation}"
        f"{successor}\n"
        f"📍 Юридический адрес: {profile.address}\n"
        f"🏷️ ОКВЭД: {profile.okved} — {profile.okved_title}\n"
        f"📞 ... • ✉️ ... • 🌐 ... {contacts}"
        f"{conflict}"
    )
