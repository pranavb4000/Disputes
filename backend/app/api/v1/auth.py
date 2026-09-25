"""Authentication endpoints: login, refresh, logout, me."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies import (
    AuditContextDep,
    AuthServiceDep,
    CurrentUserDep,
    SettingsDep,
    optional_access_claims,
    verify_browser_request,
)
from app.core.config import Settings
from app.core.responses import ApiResponse, ok
from app.core.security import AccessTokenClaims
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["Authentication"])

_ERRORS: dict[int | str, dict[str, object]] = {
    401: {"description": "Not authenticated / invalid session"},
    403: {"description": "Failed CSRF checks"},
    429: {"description": "Too many attempts / account locked"},
}


def _set_refresh_cookie(response: Response, settings: Settings, token: str, max_age: int) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path=f"{settings.api_prefix}/auth",
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path=f"{settings.api_prefix}/auth",
    )


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Log in",
    description="Verifies credentials and returns a short-lived access token. "
    "A rotating refresh token is set as an HttpOnly cookie.",
    responses=_ERRORS,
)
def login(
    body: LoginRequest, response: Response, auth: AuthServiceDep, settings: SettingsDep, ctx: AuditContextDep
) -> ApiResponse[TokenResponse]:
    result = auth.login(body.username, body.password, ctx)
    _set_refresh_cookie(response, settings, result.refresh_token, result.refresh_max_age)
    return ok(result.body)


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Refresh the session",
    description="Uses the refresh cookie to issue a new access token and rotates the cookie. "
    "Requires the X-DMS-Client: web header.",
    dependencies=[Depends(verify_browser_request)],
    responses=_ERRORS,
)
def refresh(
    request: Request, response: Response, auth: AuthServiceDep, settings: SettingsDep, ctx: AuditContextDep
) -> ApiResponse[TokenResponse]:
    result = auth.refresh(request.cookies.get(settings.refresh_cookie_name), ctx)
    _set_refresh_cookie(response, settings, result.refresh_token, result.refresh_max_age)
    return ok(result.body)


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Log out",
    description="Revokes the refresh token and the current access token.",
    dependencies=[Depends(verify_browser_request)],
    responses=_ERRORS,
)
def logout(
    request: Request,
    response: Response,
    auth: AuthServiceDep,
    settings: SettingsDep,
    ctx: AuditContextDep,
    claims: Annotated[AccessTokenClaims | None, Depends(optional_access_claims)],
) -> ApiResponse[None]:
    auth.logout(request.cookies.get(settings.refresh_cookie_name), claims, ctx)
    _clear_refresh_cookie(response, settings)
    return ok(None, "Logged out")


@router.get(
    "/me",
    response_model=ApiResponse[UserProfile],
    summary="Current user",
    description="Profile, modules and permissions of the logged-in user.",
    responses=_ERRORS,
)
def me(current: CurrentUserDep, auth: AuthServiceDep) -> ApiResponse[UserProfile]:
    return ok(auth.build_profile(current.user))
