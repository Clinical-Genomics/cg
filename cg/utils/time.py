"""Module to handle time functions"""

import time
from pathlib import Path

from cg.constants.time import SECONDS_IN_A_DAY
from cg.utils.files import get_directory_creation_time_stamp


def get_start_time() -> float:
    """Returns the current time"""
    return time.time()


def get_elapsed_time(start_time: float) -> float:
    """Determines the time elapsed since the start time"""
    return time.time() - start_time


def is_directory_older_than_days_old(directory_path: Path, days_old: int) -> bool:
    """
    Check if the directory is older than the specified number of days.
    """
    days_in_seconds = SECONDS_IN_A_DAY * days_old
    dir_creation_time_stamp: float = get_directory_creation_time_stamp(
        directory_path=directory_path
    )
    return bool(dir_creation_time_stamp < time.time() - days_in_seconds)
