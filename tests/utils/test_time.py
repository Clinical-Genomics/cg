"""Test for the time utils functions."""

import os
import time
from datetime import datetime
from pathlib import Path

import mock

from cg.constants.time import TWENTY_ONE_DAYS, TWENTY_ONE_DAYS_IN_SECONDS
from cg.utils.time import (
    is_directory_older_than_days_old,
    format_time_from_string,
    DATE_TIME_FORMAT,
    format_time_from_ctime,
)


def test_is_directory_older_than_days_old(tmp_path_factory):
    """Test whether a directory is older than a certain number of days."""
    # GIVEN a directory that is created now
    created_now_path: Path = tmp_path_factory.mktemp("created_now")

    # THEN checking whether a directory is older than 21 days returns true
    with mock.patch(
        "time.time",
        return_value=time.time() + TWENTY_ONE_DAYS_IN_SECONDS,
    ):
        assert is_directory_older_than_days_old(
            directory_path=created_now_path, days_old=TWENTY_ONE_DAYS
        )


def test_is_directory_not_older_than_days_old(tmp_path_factory):
    # GIVEN a directory that is created now
    created_now_path: Path = tmp_path_factory.mktemp("created_now")

    # THEN checking whether a directory is older than 21 days returns false
    assert not is_directory_older_than_days_old(
        directory_path=created_now_path, days_old=TWENTY_ONE_DAYS
    )


def test_format_time_from_string():
    """Test the format_time_from_string function."""
    # GIVEN a time stamp string
    time_stamp = "2021-01-01T12:00:00.000+00:00"

    # WHEN formatting the time stamp
    formatted_time = format_time_from_string(time_stamp)

    # THEN the time should be formatted correctly
    assert formatted_time == datetime(2021, 1, 1, 12, 0, 0)


def test_format_time_from_ctime(tmp_path_factory):
    """Test the format_time_from_ctime function."""
    # GIVEN a time stamp
    time_stamp: float = 1210521512.0

    # WHEN formatting the time stamp
    formatted_time = format_time_from_ctime(time_stamp)

    # THEN the time should be formatted correctly
    assert formatted_time == datetime.fromtimestamp(time_stamp)
