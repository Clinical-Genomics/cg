"""Test the Lims api"""
import datetime as dt

from requests.exceptions import HTTPError

import cg
from cg.apps.lims.api import LimsAPI


def test_get_received_date(lims_api, mocker):
    """Test to get the received date"""
    # GIVEN a lims api and a mocked sample that returns a received at date
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    date = dt.datetime.today()
    mock_instance.udf = {"Received at": date}

    # WHEN fetching the date
    res = lims_api.get_received_date(123)

    # THEN asserrt the correct date is fetched
    assert res == date


def test_get_received_date_no_sample(lims_api, mocker):
    """Test to get the received date when sample not exists"""
    # GIVEN a lims api and a mocked sample that returns a received at date
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    mock_instance.udf.get.side_effect = HTTPError()

    # WHEN fetching the date
    res = lims_api.get_received_date(123)

    # THEN assert that None is returned since a exception was raised
    assert res == None


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
