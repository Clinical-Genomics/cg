"""PDC related constants"""
from cg.utils.enums import ListEnum, IntEnum


class DSMCParameters(ListEnum):
    ARCHIVE_COMMAND: list = ["archive"]
    QUERY_COMMAND: list = ["q", "archive"]
    RETRIEVE_COMMAND: list = ["retrieve", "-replace=yes"]


class PDCExitCodes(IntEnum):
    """Exit codes for PDC commands"""

    SUCCESS: int = 0
    NO_FILES_FOUND: int = 8
