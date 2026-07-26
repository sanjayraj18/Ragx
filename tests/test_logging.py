"""Each test pins one rule: JSON in prod, pretty in dev, bound context on
every line, stdlib capture, level filtering from Settings."""

import json
import logging

import pytest
import structlog

from ragx.config import Environment, Settings
from ragx.logging import configure_logging, get_logger


@pytest.fixture(autouse=True)
def _clean_logging_state() -> None:
      yield
      structlog.reset_defaults()
      structlog.contextvars.clear_contextvars()
      logging.getLogger().handlers.clear()


def _settings(environment: Environment, log_level: str = "INFO") -> Settings:
      return Settings(_env_file=None, environment=environment, log_level=log_level)  # type: ignore[arg-type]

def test_production_logs_are_json(capsys: pytest.CaptureFixture[str]) -> None:
      configure_logging(_settings(Environment.PRODUCTION))
      get_logger("test").info("document_parsed", document_id=42)
      event = json.loads(capsys.readouterr().out.strip())
      assert event["event"] == "document_parsed"
      assert event["document_id"] == 42
      assert event["level"] == "info"


def test_development_logs_are_human_readable(capsys: pytest.CaptureFixture[str]) -> None:
      configure_logging(_settings(Environment.DEVELOPMENT))
      get_logger("test").info("document_parsed")
      assert "document_parsed" in capsys.readouterr().out


def test_bound_context_appears_on_every_line(capsys: pytest.CaptureFixture[str]) -> None:
      configure_logging(_settings(Environment.PRODUCTION))
      structlog.contextvars.bind_contextvars(request_id="req-123")
      log = get_logger("test")
      log.info("first")
      log.info("second")
      lines = capsys.readouterr().out.strip().splitlines()
      assert len(lines) == 2
      assert all(json.loads(line)["request_id"] == "req-123" for line in lines)


def test_stdlib_library_logs_join_the_stream(capsys: pytest.CaptureFixture[str]) -> None:
      configure_logging(_settings(Environment.PRODUCTION))
      logging.getLogger("some.third.party.lib").warning("library_warning")
      event = json.loads(capsys.readouterr().out.strip())
      assert event["event"] == "library_warning"
      assert event["level"] == "warning"


def test_log_level_from_settings_is_enforced(capsys: pytest.CaptureFixture[str]) -> None:
      configure_logging(_settings(Environment.PRODUCTION, log_level="ERROR"))
      get_logger("test").info("too_quiet_to_matter")
      assert capsys.readouterr().out == ""
