"""PDC related constants"""
from enum import IntEnum
from cg.utils.enums import ListEnum


class DSMCParameters(ListEnum):
    ARCHIVE_COMMAND: list = ["archive"]
    QUERY_COMMAND: list = ["q", "archive"]
    RETRIEVE_COMMAND: list = ["retrieve", "-replace=yes"]
