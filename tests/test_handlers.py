from src.bot.handlers import _dump, _extract_checko_data


def test_extract_checko_data_prefers_nested_data_block():
    extra = {
        "checko": {
            "data": {"Правопреемник": "ООО Ромашка", "Налоги": {"debt": 0}},
            "meta": {"entity": "company"},
        }
    }

    result = _extract_checko_data(extra)

    assert result["Правопреемник"] == "ООО Ромашка"
    assert "meta" not in result


def test_extract_checko_data_falls_back_to_top_level_payload():
    extra = {"checko": {"Правопреемник": "ИП Иванов"}}

    result = _extract_checko_data(extra)

    assert result["Правопреемник"] == "ИП Иванов"


def test_extract_checko_data_handles_invalid_payload():
    assert _extract_checko_data({"checko": None}) == {}
    assert _extract_checko_data({}) == {}


def test_dump_escapes_html_in_payload():
    result = _dump("Финансы", {"note": "<b>tag</b> & data"})

    assert "&lt;b&gt;tag&lt;/b&gt; &amp; data" in result
    assert "<pre>" in result
