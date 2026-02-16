from src.services.settings import get_settings


def test_get_settings_uses_tg_bot_token_alias(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "   ")
    monkeypatch.setenv("TG_BOT_TOKEN", "alias-token")
    monkeypatch.setenv("CHECKO_API_KEY", "checko")
    monkeypatch.setenv("DADATA_API_KEY", "dadata")

    settings = get_settings()

    assert settings.telegram_bot_token == "alias-token"
