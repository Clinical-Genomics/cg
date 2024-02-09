"""Timestamp fixtures."""

from datetime import MAXYEAR, datetime, timedelta

import pytest


@pytest.fixture(scope="session")
def old_timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(1900, 1, 1)


@pytest.fixture(scope="session")
def timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(2020, 5, 1)


@pytest.fixture(scope="session")
def later_timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(2020, 6, 1)


@pytest.fixture(scope="session")
def future_date() -> datetime:
    """Return a distant date in the future for which no events happen later."""
    return datetime(MAXYEAR, 1, 1, 1, 1, 1)


@pytest.fixture(scope="session")
def timestamp_now() -> datetime:
    """Return a time stamp of today's date in date time format."""
    return datetime.now()


@pytest.fixture(scope="session")
def timestamp_yesterday(timestamp_now: datetime) -> datetime:
    """Return a time stamp of yesterday's date in date time format."""
    return timestamp_now - timedelta(days=1)


@pytest.fixture(scope="session")
def timestamp_in_2_weeks(timestamp_now: datetime) -> datetime:
    """Return a time stamp 14 days ahead in time."""
    return timestamp_now + timedelta(days=14)
