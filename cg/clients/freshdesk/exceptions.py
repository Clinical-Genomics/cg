class FreshdeskException(Exception):
    """Base exception for Freshdesk errors."""

    pass


class FreshdeskAPIException(FreshdeskException):
    """The Freshdesk API returned an error."""

    pass


class FreshdeskModelException(FreshdeskException):
    """Pydantic model validation failed."""

    pass
