"""Module to handle time functions"""
import datetime
import time
from pathlib import Path


def get_start_time() -> float:
    """Returns the current time"""
    return time.time()


def get_elapsed_time(start_time: float) -> float:
    """Determines the time elapsed since the start time"""
    return time.time() - start_time


def get_file_timestamp(file_path: Path) -> datetime.datetime:
    file_mtime: float = file_path.stat().st_mtime
    return datetime.datetime.fromtimestamp(file_mtime)
