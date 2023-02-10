from datetime import datetime, timedelta

from cg.utils.date import get_timedelta_from_date, get_date_days_ago


def test_get_date_days_ago(timestamp_now: datetime):
    """Test returning a date corresponding to number of days ago."""

    # GIVEN days ago

    # WHEN calling the function
    date: datetime = get_date_days_ago(days_ago=1)

    # THEN assert the return should be a date
    assert isinstance(date, datetime)

    # Then the date returned should be less than then today
    assert date < timestamp_now


def test_get_timedelta_from_date(timestamp_yesterday: datetime):
    """Test returning the number of days ago corresponding to a given date."""

    # GIVEN a date

    # WHEN calling the function
    age: timedelta = get_timedelta_from_date(date=timestamp_yesterday)

    # THEN assert the return should be a time delta
    assert isinstance(age, timedelta)

    # Then the age in days should be yesterday
    assert age.days == 1
