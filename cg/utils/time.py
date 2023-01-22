"""Module to handle time functions"""

import time


def get_start_time() -> float:
    """Returns the current time"""
    return time.time()


def get_elapsed_time(start_time: float) -> float:
    """Determines the time elapsed since the start time"""
    return time.time() - start_time
