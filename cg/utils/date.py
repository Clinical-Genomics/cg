"""Module to parse dates."""
import datetime
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from cg.constants.symbols import DASH, DOT, FWD_SLASH, SPACE

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DATETIME_FORMAT_DATE = "%Y-%m-%d %H:%M:%S"
SIMPLE_DATE_FORMAT = "%Y-%m-%d"

LOG = logging.getLogger(__name__)


def match_date(date: str) -> bool:
    """Check if a string is a valid date."""
    date_pattern = re.compile(r"^(19|20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])")
    return bool(re.match(date_pattern, date))


def get_date(date: Optional[str] = None, date_format: Optional[str] = None) -> datetime:
    """Return a datetime object if there is a valid date.

    Raise exception if date is not valid.
    Return todays date if no date where added.

    """
    LOG.info(f"Trying to parse date string {date}")
    if not date:
        return datetime.now()

    if date_format:
        return datetime.strptime(date, date_format)

    if not match_date(date):
        raise ValueError(f"Date {date} is invalid")

    try:
        return datetime.strptime(date, DATETIME_FORMAT)
    except ValueError:
        try:
            return datetime.strptime(date, DATETIME_FORMAT_DATE)
        except ValueError:
            LOG.info("Date is not in standard format")

    for separator in [DASH, SPACE, DOT, FWD_SLASH]:
        date_parts = date.split(separator)
        if len(date_parts) == 3:
            return datetime(*(int(number) for number in date_parts))
    raise ValueError(f"Date {date} is invalid")


def get_timedelta_from_date(date: datetime) -> timedelta:
    """Return the number of days ago from date to now."""
    return datetime.now() - date


def get_date_days_ago(days_ago: int) -> datetime:
    """Return the date that was number of 'days_ago'."""
    return datetime.now() - timedelta(days=days_ago)
