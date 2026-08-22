import pytest
from pydantic import ValidationError

from app.infrastructure.settings import Settings


def test_settings_use_expected_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.log_level == "INFO"
    assert settings.log_to_file is False
    assert settings.log_file == "logs/app.log"
    assert settings.app_timezone == "America/Sao_Paulo"
    assert settings.agent_execution_timeout_seconds == 120.0
    assert settings.llm_request_timeout_seconds == 30.0


@pytest.mark.parametrize("level", ["INFO", "DEBUG"])
def test_settings_accept_valid_log_levels(level: str) -> None:
    settings = Settings(_env_file=None, log_level=level)

    assert settings.log_level == level


def test_settings_reject_invalid_log_level() -> None:
    with pytest.raises(ValidationError, match="log_level"):
        Settings(_env_file=None, log_level="WARNING")


def test_settings_reject_unknown_value() -> None:
    with pytest.raises(ValidationError, match="unexpected_setting"):
        Settings(_env_file=None, unexpected_setting="value")


@pytest.mark.parametrize(
    "field",
    ["agent_execution_timeout_seconds", "llm_request_timeout_seconds"],
)
def test_settings_reject_non_positive_timeouts(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        Settings(_env_file=None, **{field: 0})


def test_settings_reject_dummy_api_keys_at_boot() -> None:
    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="GEMINI_API_KEY, GROQ_API_KEY"):
        settings.validate_llm_api_keys()


def test_settings_accept_configured_api_keys() -> None:
    settings = Settings(
        _env_file=None,
        gemini_api_key="gemini-key",
        groq_api_key="groq-key",
    )

    settings.validate_llm_api_keys()
