"""Config tests. Every Settings() here passes _env_file=None so results
don't depend on whatever .env the developer has locally."""

import pytest
from pydantic import ValidationError

from ragx.config import Environment, Settings


def test_defaults_are_valid() -> None:
    s = Settings(_env_file=None)
    assert s.environment is Environment.DEVELOPMENT
    assert s.log_level == "INFO"


def test_env_var_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAGX_LOG_LEVEL", "ERROR")
    assert Settings(_env_file=None).log_level == "ERROR"


def test_invalid_value_fails_at_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAGX_DATABASE_URL", "not-a-url")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_debug_forbidden_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment=Environment.PRODUCTION, debug=True)


def test_settings_are_immutable() -> None:
    s = Settings(_env_file=None)
    with pytest.raises(ValidationError):
        s.debug = True  # type: ignore[misc]
