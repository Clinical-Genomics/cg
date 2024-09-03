"""Test the Lims api"""

import datetime as dt

from requests.exceptions import HTTPError

from cg.constants.lims import LimsProcess
from tests.mocks.limsmock import MockLimsAPI


def test_get_received_date(lims_mock, mocker):
    """Test to get the received date"""
    # GIVEN a lims api and a mocked sample that returns a received at date
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    date = dt.datetime.today()
    mock_instance.udf = {"Received at": date}

    # WHEN fetching the date
    res = lims_mock.get_received_date(123)

    # THEN assert the correct date is fetched
    assert res == date


def test_get_received_date_no_sample(lims_api, mocker):
    """Test to get the received date when sample not exists"""
    # GIVEN a lims api and a mocked sample that raises exception when fething date
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    mock_instance.udf.get.side_effect = HTTPError()

    # WHEN fetching the date
    res = lims_api.get_received_date(123)

    # THEN assert that None is returned since a exception was raised
    assert res is None


def test_get_prepared_date(lims_api, mocker):
    """Test to get the prepared date for an existing sample"""
    # GIVEN a lims api and a mocked sample that returns a prepared at date
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    date = dt.datetime.today()
    mock_instance.udf = {"Library Prep Finished": date}

    # WHEN fetching the date
    res = lims_api.get_prepared_date(123)

    # THEN assert the correct date is fetched
    assert res == date


def test_get_prepared_date_no_sample(lims_api, mocker):
    """Test to get the prepared date when sample not exists"""
    # GIVEN a lims api and a mocked sample that raises exception when fething date
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    mock_instance.udf.get.side_effect = HTTPError()

    # WHEN fetching the date
    res = lims_api.get_prepared_date(123)

    # THEN assert that None is returned since a exception was raised
    assert res is None


def test_get_delivery_date(lims_api, mocker):
    """Test to get the delivery date for an existing sample"""
    # GIVEN a lims api and a mocked sample that returns a delivery date
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    date = dt.datetime.today()
    mock_instance.udf = {"Delivered at": date}

    # WHEN fetching the date
    res = lims_api.get_delivery_date(123)

    # THEN assert the correct date is fetched
    assert res == date


def test_get_delivery_date_no_sample(lims_api, mocker):
    """Test to get the delivery date when sample not exists"""
    # GIVEN a lims api and a mocked sample that raises exception when fething date
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    mock_instance.udf.get.side_effect = HTTPError()

    # WHEN fetching the date
    res = lims_api.get_delivery_date(123)

    # THEN assert that None is returned since a exception was raised
    assert res is None


def test_get_internal_negative_control_id_from_sample_in_pool(
    lims_api_with_sample_and_internal_negative_control: MockLimsAPI,
):
    # GIVEN a sample_id
    sample_id: str = "sample"

    # WHEN retrieving the internal_negative_control_id_from_lims
    internal_negative_control_id = lims_api_with_sample_and_internal_negative_control.get_internal_negative_control_id_from_sample_in_pool(
        sample_internal_id=sample_id, pooling_step=LimsProcess.COVID_POOLING_STEP
    )

    # THEN no errors are raised and the correct internal_negative_control_id is retrieved
    assert internal_negative_control_id == "internal_negative_control"
