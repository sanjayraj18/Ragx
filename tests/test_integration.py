import pytest
from fastapi.testclient import TestClient

from ragx.api.app import create_app
from ragx.config import Environment, Settings

pytestmark = pytest.mark.integration


def test_readyz_is_ready_with_real_database() -> None:
      settings = Settings(_env_file=None, environment=Environment.TEST)
      with TestClient(create_app(settings)) as client:
          response = client.get("/readyz")
      assert response.status_code == 200
      assert response.json() == {"status": "ready"}
