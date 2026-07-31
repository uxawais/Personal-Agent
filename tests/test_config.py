import pytest
from agent.config import Settings


def test_settings_defaults():
    s = Settings(
        _env_file=None,
        OPENAI_API_KEY="",
        ANTHROPIC_API_KEY="",
        AWS_ACCESS_KEY_ID="",
        AWS_SECRET_ACCESS_KEY="",
        GEMINI_API_KEY="",
    )
    assert s.APP_NAME == "Chorus Agent"
    assert s.APP_PORT == 8000
    assert s.DEFAULT_PROVIDER == "openai"
    assert s.ROUTING_STRATEGY == "smart"


def test_slack_allowed_ids_parsing():
    s = Settings(
        _env_file=None,
        SLACK_ALLOWED_USER_IDS="U123, U456, U789",
        OPENAI_API_KEY="",
        ANTHROPIC_API_KEY="",
        AWS_ACCESS_KEY_ID="",
        AWS_SECRET_ACCESS_KEY="",
        GEMINI_API_KEY="",
    )
    assert s.slack_allowed_user_ids_list == ["U123", "U456", "U789"]


def test_whatsapp_allowed_numbers_parsing():
    s = Settings(
        _env_file=None,
        WHATSAPP_ALLOWED_PHONE_NUMBERS="+1234567890,+0987654321",
        OPENAI_API_KEY="",
        ANTHROPIC_API_KEY="",
        AWS_ACCESS_KEY_ID="",
        AWS_SECRET_ACCESS_KEY="",
        GEMINI_API_KEY="",
    )
    assert s.whatsapp_allowed_numbers_list == ["+1234567890", "+0987654321"]


def test_empty_allowed_ids():
    s = Settings(
        _env_file=None,
        SLACK_ALLOWED_USER_IDS="",
        WHATSAPP_ALLOWED_PHONE_NUMBERS="",
        OPENAI_API_KEY="",
        ANTHROPIC_API_KEY="",
        AWS_ACCESS_KEY_ID="",
        AWS_SECRET_ACCESS_KEY="",
        GEMINI_API_KEY="",
    )
    assert s.slack_allowed_user_ids_list == []
    assert s.whatsapp_allowed_numbers_list == []
