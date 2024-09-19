"""Error for the database module."""

from cg.exc import CgError


class EntryAlreadyExistsError(CgError):
    """Error for when an entry already exists in the database."""


class EntryNotFoundError(CgError):
    """Error for when an entry is not found in the database."""
