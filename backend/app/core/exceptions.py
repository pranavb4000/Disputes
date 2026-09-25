"""Application errors and centralised exception handlers (TECH_STACK.md §13).

Clients only ever see the standard envelope with a safe message and an error_code.
Stack traces, SQL and infrastructure details go to the server log only.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.responses import error_body

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "BAD_REQUEST"
    message: str = "The request could not be processed"

    def __init__(self, message: str | None = None, *, error_code: str | None = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message
        if error_code:
            self.error_code = error_code


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"
    message = "Authentication required"


class InvalidCredentialsError(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid username or password"


class TokenError(AuthenticationError):
    error_code = "INVALID_TOKEN"
    message = "Your session is invalid or has expired. Please log in again."


class PermissionDeniedError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action"


class CsrfError(PermissionDeniedError):
    error_code = "CSRF_CHECK_FAILED"
    message = "Request rejected by security checks"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "RESOURCE_NOT_FOUND"
    message = "Resource not found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"
    message = "The resource was changed by someone else"


class RateLimitedError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "TOO_MANY_REQUESTS"
    message = "Too many attempts. Please try again later."


class ServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"
    message = "A dependent service is unavailable"


_HTTP_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "RESOURCE_NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    429: "TOO_MANY_REQUESTS",
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(error_body(exc.message, exc.error_code), status_code=exc.status_code, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Field paths and messages only; never echo the submitted values (they may contain passwords).
        errors = [
            {"field": ".".join(str(p) for p in err.get("loc", ()) if p != "body"), "message": err.get("msg", "")}
            for err in exc.errors()
        ]
        return JSONResponse(
            error_body("Validation failed", "VALIDATION_ERROR", {"errors": errors}),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(error_body(message, code), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", extra={"error_type": type(exc).__name__})
        return JSONResponse(
            error_body("An unexpected error occurred. Please contact support with the request ID.", "INTERNAL_ERROR"),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
