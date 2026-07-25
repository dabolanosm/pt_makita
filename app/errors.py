from __future__ import annotations


class ExternalAPIError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(Exception):
    def __init__(self, message: str = "Not found", status_code: int = 404) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(Exception):
    def __init__(self, message: str = "Validation error", status_code: int = 422) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)
