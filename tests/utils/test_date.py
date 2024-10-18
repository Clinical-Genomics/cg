from datetime import datetime, timedelta

from cg.utils.date import (
    convert_string_to_datetime_object,
    get_date_days_ago,
    get_timedelta_from_date,
)


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


def test_convert_string_to_datetime_object_valid():
    # GIVEN a list of valid datetime strings with different formats
    valid_datetime_strings = [
        ("10/15/2024 12:45:30", "%m/%d/%Y %H:%M:%S"),  # Month/Day/Year, U.S. format
    ]

    # WHEN the function is called with valid strings
    for date_str, expected_format in valid_datetime_strings:
        # THEN it should return the correct datetime object
        expected_datetime = datetime.strptime(date_str, expected_format)
        assert convert_string_to_datetime_object(date_str) == expected_datetime


def test_convert_string_to_datetime_object_invalid():
    # GIVEN a list of invalid datetime strings
    invalid_datetime_strings = [
        "2024-15-10 12:45:30",  # Invalid day format
        "15-10-2024 12:45",  # Missing seconds
        "Invalid string",  # Completely invalid
    ]

    # WHEN the function is called with invalid strings
    for date_str in invalid_datetime_strings:
        # THEN it should raise a ValueError
        try:
            convert_string_to_datetime_object(date_str)
            assert False, f"Expected ValueError for {date_str} but it didn't raise"
        except ValueError as e:
            assert str(e) == f"Could not convert '{date_str}' to a datetime object."
