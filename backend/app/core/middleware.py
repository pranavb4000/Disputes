"""Request context: request ID propagation, timing and one structured log line per request."""

from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_var, user_id_var

logger = logging.getLogger("app.request")
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9\-_.]{8,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get("X-Request-ID", "")
        request_id = incoming if _SAFE_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        rid_token = request_id_var.set(request_id)
        uid_token = user_id_var.set(None)
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": request.client.host if request.client else None,
                    "user_id": getattr(request.state, "user_id", None),
                },
            )
            request_id_var.reset(rid_token)
            user_id_var.reset(uid_token)
        response.headers["X-Request-ID"] = request_id
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response
