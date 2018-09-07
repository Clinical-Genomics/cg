import datetime as dt


def test_get_last_day_of_month_newyearseve(sample_store):

    # GIVEN

    # WHEN calling get_until_date
    day = dt.datetime(2001, 12, 31)
    until_date = sample_store.get_until_date(day.year)

    # THEN return should be last december of that year
    assert day.year == until_date.year
    assert 12 == until_date.month
    assert 31 == until_date.day


def test_get_last_day_of_month_1stjanuary(sample_store):

    # GIVEN

    # WHEN calling get_last_day_of_month with 2001-01-01
    day = dt.datetime(2001, 1, 1)
    until_date = sample_store.get_until_date(day.year)

    # THEN return should be 2001-01-31
    assert day.year == until_date.year
    assert 12 == until_date.month
    assert 31 == until_date.day
