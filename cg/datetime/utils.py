"""Module for datetime utility functions."""
from datetime import datetime, timedelta


def get_date_days_ago(days_ago: int) -> datetime:
    """Return the date that was number of 'days_ago'."""
    return datetime.now() - timedelta(days=days_ago)


def get_timedelta_from_date(date: datetime) -> timedelta:
    """Return the number of days ago from date to now."""
    return datetime.now() - date
