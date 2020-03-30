import datetime as dt


def test_get_processing_time_for_values(lims_api):

    # GIVEN there is a received_at date and a delivered date
    date = dt.datetime.today()
    lims_api.set_received_date(date)
    lims_api.set_delivery_date(date)

    # WHEN calling get_processing_time
    processing_time = lims_api.get_processing_time(123)

    # THEN return value is the delivered - received == 0 for same datetime
    assert processing_time == dt.timedelta(0)


def test_get_processing_time_for_no_received_time(lims_api):

    # GIVEN there is no received_at date and a delivered date
    date = dt.datetime.today()
    lims_api.set_delivery_date(date)

    # WHEN calling get_processing_time
    processing_time = lims_api.get_processing_time(123)

    # THEN return value is none
    assert processing_time is None


def test_get_processing_time_for_no_delivered_time(lims_api):

    # GIVEN there is a received_at date and no delivered date
    date = dt.datetime.today()
    lims_api.set_received_date(date)

    # WHEN calling get_processing_time
    processing_time = lims_api.get_processing_time(123)

    # THEN return value is none
    assert processing_time is None
