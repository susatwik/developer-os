"""Developer OS error types."""

from __future__ import annotations


class DeveloperOSError(Exception):
    """Base error for Developer OS."""


class ConfigurationError(DeveloperOSError):
    """Raised when required configuration is missing or invalid."""


class ExternalServiceError(DeveloperOSError):
    """Raised when an upstream API request fails."""


class RateLimitError(ExternalServiceError):
    """Raised when an API rate limit is hit."""

