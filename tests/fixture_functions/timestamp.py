"""Timestamps fixtures."""
from datetime import MAXYEAR, datetime, timedelta

import pytest


@pytest.fixture(name="old_timestamp", scope="session")
def fixture_old_timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(1900, 1, 1)


@pytest.fixture(name="timestamp", scope="session")
def fixture_timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(2020, 5, 1)


@pytest.fixture(name="later_timestamp", scope="session")
def fixture_later_timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(2020, 6, 1)


@pytest.fixture(name="future_date", scope="session")
def fixture_future_date() -> datetime:
    """Return a distant date in the future for which no events happen later."""
    return datetime(MAXYEAR, 1, 1, 1, 1, 1)


@pytest.fixture(name="timestamp_now", scope="session")
def fixture_timestamp_now() -> datetime:
    """Return a time stamp of today's date in date time format."""
    return datetime.now()


@pytest.fixture(name="timestamp_yesterday", scope="session")
def fixture_timestamp_yesterday(timestamp_now: datetime) -> datetime:
    """Return a time stamp of yesterday's date in date time format."""
    return timestamp_now - timedelta(days=1)


@pytest.fixture(name="timestamp_in_2_weeks", scope="session")
def fixture_timestamp_in_2_weeks(timestamp_now: datetime) -> datetime:
    """Return a time stamp 14 days ahead in time."""
    return timestamp_now + timedelta(days=14)
