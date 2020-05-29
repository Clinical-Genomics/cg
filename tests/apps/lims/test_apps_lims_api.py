"""Test the Lims api"""
import datetime as dt

from cg.apps.lims.api import LimsAPI


def test_get_processing_time_for_values(lims_api, mocker):
    """Test to get the processing time when there are some existing dates"""
    # GIVEN there is a received_at date and a delivered date
    date = dt.datetime.today()
    # GIVEN that received and delivered date is the same
    mocker.patch.object(LimsAPI, "get_received_date")
    LimsAPI.get_received_date.return_value = date

    mocker.patch.object(LimsAPI, "get_delivery_date")
    LimsAPI.get_delivery_date.return_value = date

    # WHEN fetching the processing time
    processing_time = lims_api.get_processing_time(123)

    # THEN return value is the delivered - received == 0 for same datetime
    assert processing_time == dt.timedelta(0)


def test_get_processing_time_for_no_received_time(lims_api, mocker):
    """Test to get the processing time when there is not received time"""
    # GIVEN there is no received_at date
    mocker.patch.object(LimsAPI, "get_received_date")
    LimsAPI.get_received_date.return_value = None
    # GIVEN there is a delivery date
    date = dt.datetime.today()
    mocker.patch.object(LimsAPI, "get_delivery_date")
    LimsAPI.get_delivery_date.return_value = date

    # WHEN calling get_processing_time
    processing_time = lims_api.get_processing_time(123)

    # THEN return value should be none since one time is missing
    assert processing_time is None


def test_get_processing_time_for_no_delivered_time(lims_api, mocker):
    """Test to get the processing time when there is not delivered time"""

    # GIVEN there is a received_at date and no delivered date
    date = dt.datetime.today()
    mocker.patch.object(LimsAPI, "get_received_date")
    LimsAPI.get_received_date.return_value = date

    mocker.patch.object(LimsAPI, "get_delivery_date")
    LimsAPI.get_delivery_date.return_value = None

    # WHEN calling get_processing_time
    processing_time = lims_api.get_processing_time(123)

    # THEN return value is none
    assert processing_time is None
