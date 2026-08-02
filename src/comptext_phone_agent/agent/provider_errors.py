from __future__ import annotations

from typing import TypeVar

import httpx


STATUS_CATEGORIES = {
    401: "authentication",
    403: "authorization",
    404: "not_found",
    429: "rate_limited",
}


class ProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        category: str = "provider_error",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.status_code = status_code


ErrorType = TypeVar("ErrorType", bound=ProviderError)


def classify_provider_error(
    error: Exception,
    *,
    label: str,
    error_type: type[ErrorType] = ProviderError,
) -> ErrorType:
    status_code: int | None = None
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code
        category = STATUS_CATEGORIES.get(status_code, "http_error")
    elif isinstance(error, httpx.TimeoutException):
        category = "timeout"
    elif isinstance(error, httpx.RequestError):
        category = "network"
    else:
        category = "invalid_response"
    message = f"{label} request failed ({category})"
    return error_type(message, category=category, status_code=status_code)
