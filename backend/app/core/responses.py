"""The single, central API response contract (TECH_STACK.md §11).

Success:  {"success": true,  "data": {...}, "message": null}
Error:    {"success": false, "data": null,  "message": "...", "error_code": "..."}
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None
    error_code: str | None = None


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=500)
    total: int = Field(ge=0)


def ok(data: T | None = None, message: str | None = None) -> ApiResponse[T]:
    return ApiResponse[T](success=True, data=data, message=message)


def error_body(message: str, error_code: str, data: object | None = None) -> dict[str, object]:
    return {"success": False, "data": data, "message": message, "error_code": error_code}
