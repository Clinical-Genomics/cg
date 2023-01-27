"""Module for datetime utility functions."""
from datetime import datetime, timedelta


def get_date_days_ago(days_ago: int) -> datetime:
    """Calculate the date 'days_ago'."""
    return datetime.now() - timedelta(days=days_ago)
