"""Module to handle time functions"""

import time
import re
from datetime import datetime
from pathlib import Path

from cg.constants.time import SECONDS_IN_A_DAY
from cg.utils.files import get_source_creation_time_stamp

DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def get_start_time() -> float:
    """Returns the current time"""
    return time.time()


def format_time(time: str) -> datetime:
    """Format the time by removing microseconds and time zone."""
    no_microseconds: str = re.sub(r"\.\d+", "", time)
    no_microseconds_no_time_zone = re.sub(r"[+-]\d{2}:\d{2}$", "", no_microseconds)
    return datetime.strptime(no_microseconds_no_time_zone, DATE_TIME_FORMAT)


def get_elapsed_time(start_time: float) -> float:
    """Determines the time elapsed since the start time"""
    return time.time() - start_time


def is_directory_older_than_days_old(directory_path: Path, days_old: int) -> bool:
    """
    Check if the directory is older than the specified number of days.
    """
    days_in_seconds = SECONDS_IN_A_DAY * days_old
    dir_creation_time_stamp: float = get_source_creation_time_stamp(source_path=directory_path)
    return bool(dir_creation_time_stamp < time.time() - days_in_seconds)
