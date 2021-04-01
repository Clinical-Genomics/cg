"""Module to parse dates"""
import datetime
import logging
import re
from typing import Optional

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DATETIME_FORMAT_DATE = "%Y-%m-%d %H:%M:%S"
SIMPLE_DATE_FORMAT = "%Y-%m-%d"

SPACE = " "
DASH = "-"
DOT = "."
FWD_SLASH = "/"

LOG = logging.getLogger(__name__)


def match_date(date: str) -> bool:
    """Check if a string is a valid date"""
    date_pattern = re.compile(r"^(19|20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])")
    return bool(re.match(date_pattern, date))


def get_date(date: Optional[str] = None, date_format: Optional[str] = None) -> datetime.datetime:
    """Return a datetime object if there is a valid date

    Raise exception if date is not valid
    Return todays date if no date where added

    Args:
        date(str)
        date_format(str)

    Returns:
        date_obj(datetime.datetime)
    """
    LOG.info("Trying to parse date string %s", date)
    if not date:
        return datetime.datetime.now()

    if date_format:
        return datetime.datetime.strptime(date, date_format)

    if not match_date(date):
        raise ValueError("Date %s is invalid" % date)

    # Try datetimes own format
    try:
        return datetime.datetime.strptime(date, DATETIME_FORMAT)
    except ValueError:
        try:
            return datetime.datetime.strptime(date, DATETIME_FORMAT_DATE)
        except ValueError:
            LOG.info("Date is not in std format")

    for separator in [DASH, SPACE, DOT, FWD_SLASH]:
        date_parts = date.split(separator)
        if len(date_parts) == 3:
            return datetime.datetime(*(int(number) for number in date_parts))

    raise ValueError("Date %s is invalid" % date)


def get_date_str(date_time_obj: datetime.datetime = None, date_format: str = None) -> str:
    """Convert a datetime object to a string. Defaults to simple date string: 2020-06-15"""
    if date_format is None:
        date_format = SIMPLE_DATE_FORMAT
    if date_time_obj is None:
        date_time_obj = datetime.datetime.now()
    return date_time_obj.strftime(date_format)
