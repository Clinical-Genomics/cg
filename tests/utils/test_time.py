"""Test for the time utils functions."""
import time
from pathlib import Path

from cg.constants.time import TWENTY_ONE_DAYS_IN_SECONDS, TWENTY_ONE_DAYS
from cg.utils.time import is_directory_older_than_days_old


def test_is_directory_older_than_days_old(tmp_path_factory):
    """Test whether a directory is older than a certain number of days."""
    # GIVEN a directory that is created now
    created_now_path: Path = tmp_path_factory.mktemp("created_now")

    # GIVEN a current time that is 21 days ahead in seconds
    time_21_days_ahead: float = time.time() + TWENTY_ONE_DAYS_IN_SECONDS

    # THEN checking whether a directory is older than 21 days returns true
    assert is_directory_older_than_days_old(
        directory_path=created_now_path, days_old=TWENTY_ONE_DAYS, current_time=time_21_days_ahead
    )


def test_is_directory_not_older_than_days_old(tmp_path_factory):
    # GIVEN a directory that is created now
    created_now_path: Path = tmp_path_factory.mktemp("created_now")

    # GIVEN a current time that is now
    current_time: float = time.time()

    # THEN checking whether a directory is older than 21 days returns false
    assert not is_directory_older_than_days_old(
        directory_path=created_now_path, days_old=TWENTY_ONE_DAYS, current_time=current_time
    )
