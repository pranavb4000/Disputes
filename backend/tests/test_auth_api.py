"""Authentication and authorisation tests (TECH_STACK.md §19 minimum set, plus session handling)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import create_access_token
from tests.conftest import PASSWORD, WEB_HEADERS, auth_header, login
from tests.fakes import FakeRedis


def test_login_with_valid_credentials_returns_token_and_cookie(client: TestClient, settings: Settings) -> None:
    response = login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["token_type"] == "Bearer"
    assert body["data"]["user"]["username"] == "dev_user"
    assert body["data"]["user"]["modules"][0]["code"] == "UPI"
    cookie = response.headers["set-cookie"]
    assert settings.refresh_cookie_name in cookie
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Path=/api/v1/auth" in cookie


def test_login_with_invalid_password_is_rejected(client: TestClient) -> None:
    response = login(client, password="wrong-password")
    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "Invalid username or password",
        "error_code": "INVALID_CREDENTIALS",
    }


def test_login_unknown_and_disabled_users_get_the_same_error(client: TestClient) -> None:
    assert login(client, username="nobody").json()["error_code"] == "INVALID_CREDENTIALS"
    assert login(client, username="disabled_user").json()["error_code"] == "INVALID_CREDENTIALS"


def test_login_validation_error_does_not_echo_password(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={"username": "bad user!", "password": "secret-value"})
    assert response.status_code == 422
    assert "secret-value" not in response.text
    assert response.json()["error_code"] == "VALIDATION_ERROR"


def test_account_locks_after_repeated_failures(client: TestClient) -> None:
    for _ in range(3):  # LOGIN_MAX_FAILURES=3 in tests
        assert login(client, password="nope").status_code == 401
    locked = login(client)  # even the right password is refused while locked
    assert locked.status_code == 429
    assert locked.json()["error_code"] == "ACCOUNT_LOCKED"


def test_me_requires_a_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHORIZED"


def test_me_with_valid_token(client: TestClient) -> None:
    token = login(client).json()["data"]["access_token"]
    response = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert response.status_code == 200
    upi = response.json()["data"]["modules"][0]
    assert upi["roles"] == ["ADMIN", "MAKER"]
    assert "dispute.view" in upi["permissions"]


def test_invalid_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_header("not-a-jwt"))
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"


def test_token_signed_with_other_secret_is_rejected(client: TestClient, settings: Settings) -> None:
    forged = jwt.encode(
        {"sub": "1", "iss": settings.jwt_issuer, "iat": 0, "exp": 9999999999, "jti": "x", "typ": "access"},
        "another-secret" * 8,
        algorithm="HS512",
    )
    assert client.get("/api/v1/auth/me", headers=auth_header(forged)).status_code == 401


def test_token_with_weaker_algorithm_is_rejected(client: TestClient, settings: Settings) -> None:
    downgraded = jwt.encode(
        {"sub": "1", "iss": settings.jwt_issuer, "iat": 0, "exp": 9999999999, "jti": "x", "typ": "access"},
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    assert client.get("/api/v1/auth/me", headers=auth_header(downgraded)).status_code == 401


def test_expired_token_is_rejected(client: TestClient, settings: Settings) -> None:
    user_id = login(client).json()["data"]["user"]["id"]
    old = datetime.now(UTC) - timedelta(hours=2)
    token, _ = create_access_token(settings, user_id=user_id, username="dev_user", roles={}, now=old)
    response = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"


def test_insufficient_permissions_on_module(client: TestClient) -> None:
    token = login(client, username="no_roles").json()["data"]["access_token"]
    response = client.get("/api/v1/upi/summary", headers=auth_header(token))
    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


def test_permission_granted_on_module(client: TestClient) -> None:
    token = login(client).json()["data"]["access_token"]
    response = client.get("/api/v1/upi/summary", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json()["data"]["module_code"] == "UPI"


def test_disabled_module_is_forbidden_even_with_token(client: TestClient) -> None:
    token = login(client).json()["data"]["access_token"]
    assert client.get("/api/v1/imps/summary", headers=auth_header(token)).status_code == 403


def test_refresh_rotates_the_cookie(client: TestClient, settings: Settings) -> None:
    login(client)
    first_cookie = client.cookies.get(settings.refresh_cookie_name)
    response = client.post("/api/v1/auth/refresh", headers=WEB_HEADERS)
    assert response.status_code == 200
    assert response.json()["data"]["access_token"]
    assert client.cookies.get(settings.refresh_cookie_name) != first_cookie


def test_refresh_requires_client_header(client: TestClient) -> None:
    login(client)
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 403
    assert response.json()["error_code"] == "CSRF_CHECK_FAILED"


def test_refresh_rejects_foreign_origin(client: TestClient) -> None:
    login(client)
    response = client.post("/api/v1/auth/refresh", headers={**WEB_HEADERS, "Origin": "https://evil.example"})
    assert response.status_code == 403


def test_refresh_without_cookie_is_unauthorised(client: TestClient) -> None:
    assert client.post("/api/v1/auth/refresh", headers=WEB_HEADERS).status_code == 401


def test_reused_refresh_token_revokes_the_session(client: TestClient, settings: Settings, redis: FakeRedis) -> None:
    login(client)
    stolen = client.cookies.get(settings.refresh_cookie_name)
    assert client.post("/api/v1/auth/refresh", headers=WEB_HEADERS).status_code == 200
    # Pretend the grace window (for parallel tabs) has passed, then replay the old token.
    for key in [k for k in list(redis._data) if ":rtused:" in k]:
        record = json.loads(redis._data[key])
        record["used_at"] -= 3600
        redis._data[key] = json.dumps(record)
    client.cookies.set(settings.refresh_cookie_name, stolen, path="/api/v1/auth")
    assert client.post("/api/v1/auth/refresh", headers=WEB_HEADERS).status_code == 401
    # The legitimate (rotated) token is now dead too: the whole family was revoked.
    assert not any(":rtfam:" in k for k in redis._data)


def test_logout_revokes_access_and_refresh(client: TestClient) -> None:
    token = login(client).json()["data"]["access_token"]
    response = client.post("/api/v1/auth/logout", headers={**WEB_HEADERS, **auth_header(token)})
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out"
    assert client.get("/api/v1/auth/me", headers=auth_header(token)).status_code == 401
    assert client.post("/api/v1/auth/refresh", headers=WEB_HEADERS).status_code == 401


def test_login_and_logout_are_audited(client: TestClient) -> None:
    token = login(client).json()["data"]["access_token"]
    login(client, password=PASSWORD + "x")
    client.post("/api/v1/auth/logout", headers={**WEB_HEADERS, **auth_header(token)})
    token = login(client).json()["data"]["access_token"]
    activity = client.get("/api/v1/home", headers=auth_header(token)).json()["data"]["recent_activity"]
    actions = [(a["action"], a["outcome"]) for a in activity]
    assert ("LOGOUT", "SUCCESS") in actions and ("LOGIN", "SUCCESS") in actions
