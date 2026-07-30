"""Shared fixtures for the whole suite.

conftest.py is discovered by pytest automatically; fixtures defined here
are available to every test without imports. Unit tests need no
infrastructure; integration-marked tests expect `docker compose up -d`.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ragx.api.app import create_app
from ragx.config import Environment, Settings


@pytest.fixture
def test_settings() -> Settings:
    return Settings(_env_file=None, environment=Environment.TEST)


@pytest.fixture
def client(test_settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(test_settings), raise_server_exceptions=False) as c:
        yield c
