from src.bot.formatters import format_card
from src.services.aggregator import Profile


def test_format_card_contains_core_fields():
    profile = Profile(
        inn="3525405517",
        short_name='ООО "Тест"',
        full_name='Общество с ограниченной ответственностью "Тест"',
        ogrn="1234567890123",
        kpp="123456789",
        status="ACTIVE",
        registration_date="2010-01-01",
        liquidation_date="",
        address="г. Москва",
        manager="Иванов И.И.",
        capital="10000",
        okved="62.01",
        okved_title="Разработка компьютерного программного обеспечения",
        contacts=["+79990001122", "test@example.com"],
        successor="",
        source_dispute=False,
    )

    text = format_card(profile)
    assert "Готово ✅" in text
    assert "3525405517" in text
    assert "62.01" in text


def test_format_card_escapes_html_sensitive_data():
    profile = Profile(
        inn="3525405517",
        short_name='<b>ООО "Тест"</b>',
        full_name='Общество "<Тест>"',
        ogrn="1234567890123",
        kpp="123456789",
        status="ACTIVE",
        registration_date="2010-01-01",
        liquidation_date="",
        address='ул. <Садовая> & д. 1',
        manager='Иванов <script>alert(1)</script>',
        capital="10000",
        okved="62.01",
        okved_title="Разработка <ПО>",
        contacts=['https://example.com?a=1&b=2'],
        successor="",
        source_dispute=False,
    )

    text = format_card(profile)

    assert "&lt;b&gt;ООО &quot;Тест&quot;&lt;/b&gt;" in text
    assert "Иванов &lt;script&gt;alert(1)&lt;/script&gt;" in text
    assert "https://example.com?a=1&amp;b=2" in text
