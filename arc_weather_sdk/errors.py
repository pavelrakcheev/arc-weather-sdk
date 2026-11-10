"""Errors raised by the Arc Weather SDK."""


class ArcWeatherError(Exception):
    """Base class for every error raised by the SDK."""


class AuthenticationError(ArcWeatherError):
    """The API key is missing, unknown or not allowed to use the operation."""


class RateLimitError(ArcWeatherError):
    """The key exceeded its quota. ``retry_after`` holds the wait in seconds."""

    def __init__(self, message: str, *, retry_after: int = 0) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ApiError(ArcWeatherError):
    """The service answered with an error status."""

    def __init__(self, message: str, *, status_code: int = 0, detail: object = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class NotFoundError(ApiError):
    """The requested resource does not exist."""
