"""Test the Lims api"""
import datetime as dt

from requests.exceptions import HTTPError

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

    # THEN asserrt the correct date is fetched
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

    # THEN asserrt the correct date is fetched
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


def test_get_rin(lims_api, mocker):
    """Test to get the RIN value of a sample."""
    # GIVEN a lims api and a mocked sample that returns a RIN value
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    rin_value = 6.8
    mock_instance.udf = {"RIN": rin_value}

    # WHEN fetching the RIN value
    res = lims_api.get_sample_rin(123)

    # THEN assert the correct value is fetched
    assert res == rin_value


def test_get_rin_no_value(lims_api, mocker):
    """Test to get a non-existent RIN value of a sample."""
    # GIVEN a lims api and a mocked sample that doesn't have a RIN value
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value

    # WHEN fetching the RIN value
    res = lims_api.get_sample_rin(123)

    # THEN assert that None is returned
    assert res is None


def test_get_rin_no_sample(lims_api, mocker):
    """Test to get a RIN value of a non-existent sample."""
    # GIVEN a lims api and a mocked sample that doesn't have a RIN value
    mocked_sample = mocker.patch("cg.apps.lims.api.Sample")
    mock_instance = mocked_sample.return_value
    mock_instance.udf.get.side_effect = HTTPError()

    # WHEN fetching the RIN value
    res = lims_api.get_sample_rin(123)

    # THEN assert that None is returned since an exception was raised
    assert res is None
