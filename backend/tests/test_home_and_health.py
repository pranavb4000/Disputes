"""Home page, health endpoints and the response envelope."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_header, login


def test_home_requires_login(client: TestClient) -> None:
    assert client.get("/api/v1/home").status_code == 401


def test_home_summary(client: TestClient) -> None:
    token = login(client).json()["data"]["access_token"]
    response = client.get("/api/v1/home", headers=auth_header(token))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["greeting_name"] == "Developer"
    cards = {c["code"]: c for c in data["modules"]}
    assert cards["UPI"]["has_access"] is True and cards["UPI"]["is_enabled"] is True
    assert cards["IMPS"]["has_access"] is False
    assert data["recent_activity"][0]["action"] == "LOGIN"
    assert data["recent_activity"][0]["occurred_at"].endswith("Z")


def test_liveness(client: TestClient) -> None:
    body = client.get("/api/v1/health").json()
    assert body["success"] is True and body["data"]["status"] == "ok"


def test_unknown_route_uses_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does/not/exist/at/all")
    assert response.status_code == 404
    assert response.json()["success"] is False


def test_request_id_is_returned_and_api_responses_are_not_cached(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "abc12345-test"})
    assert response.headers["X-Request-ID"] == "abc12345-test"
    assert response.headers["Cache-Control"] == "no-store"
