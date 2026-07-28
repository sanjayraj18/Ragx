from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from ragx.api.app import create_app
from ragx.api.deps import get_session
from ragx.config import Environment, Settings
from ragx.errors import NotFoundError


def _settings(**overrides: object) -> Settings:
      return Settings(_env_file=None, environment=Environment.TEST, **overrides)  # type: ignore[arg-type]


def test_each_call_builds_a_fresh_private_app() -> None:
      first = create_app(_settings())
      second = create_app(_settings())
      assert first is not second


def test_settings_choose_the_apps_behavior() -> None:
      quiet = create_app(_settings(debug=False))
      loud = create_app(_settings(debug=True))
      assert quiet.debug is False
      assert loud.debug is True

def test_domain_error_maps_to_status_and_envelope() -> None:
      app = create_app(_settings())

      @app.get("/boom")
      async def boom() -> None:
          raise NotFoundError("document 42 does not exist")

      response = TestClient(app, raise_server_exceptions=False).get("/boom")
      assert response.status_code == 404
      assert response.json() == {
          "error": {"code": "not_found", "message": "document 42 does not exist"}
      }


def test_unexpected_error_returns_500_and_never_leaks() -> None:
      app = create_app(_settings())

      @app.get("/crash")
      async def crash() -> None:
          raise RuntimeError("secret-database-password-in-traceback")

      response = TestClient(app, raise_server_exceptions=False).get("/crash")
      assert response.status_code == 500
      assert "secret" not in response.text
      assert response.json()["error"]["code"] == "internal_error"

def test_healthz_ok() -> None:
      response = TestClient(create_app(_settings())).get("/healthz")
      assert response.status_code == 200
      assert response.json() == {"status": "ok"}


class _FakeSession:
      """A stand-in session whose SELECT 1 always succeeds — the DB is 'reachable'."""

      async def execute(self, _statement: object) -> None:
          return None


def test_readyz_ok() -> None:
      app = create_app(_settings())

      async def fake_session() -> AsyncIterator[_FakeSession]:
          yield _FakeSession()

      app.dependency_overrides[get_session] = fake_session

      response = TestClient(app).get("/readyz")
      assert response.status_code == 200
      assert response.json() == {"status": "ready"}


def test_every_response_carries_a_request_id() -> None:
      response = TestClient(create_app(_settings())).get("/healthz")
      assert response.headers["x-request-id"]


def test_callers_request_id_is_echoed_back() -> None:
      response = TestClient(create_app(_settings())).get(
          "/healthz", headers={"X-Request-ID": "req-from-caller"}
      )
      assert response.headers["x-request-id"] == "req-from-caller"


def test_unknown_route_uses_the_same_envelope() -> None:
      response = TestClient(create_app(_settings())).get("/no-such-path")
      assert response.status_code == 404
      assert response.json()["error"]["code"] == "http_error"

def test_readyz_reports_not_ready_when_database_is_unreachable() -> None:
      with TestClient(create_app(_settings())) as client:
          response = client.get("/readyz")
      assert response.status_code == 503
      assert response.json() == {"status": "not_ready"}
