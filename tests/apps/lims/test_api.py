"""Test the Lims api"""

import datetime as dt
from unittest.mock import create_autospec

import pytest
from genologics import entities
from genologics.descriptors import EntityDescriptor
from genologics.entities import Artifact, Sample
from genologics.lims import Lims
from pytest_mock import MockerFixture
from requests.exceptions import HTTPError

from cg.apps.lims import LimsAPI
from cg.constants.lims import LimsArtifactTypes, LimsProcess
from cg.exc import LimsDataError
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture
def config_for_lims_api() -> dict:
    """Fixture to provide a config dict for the LimsAPI."""
    return {
        "lims": {
            "host": "https://lims.scilifelab.se",
            "username": "user",
            "password": "password",
        }
    }


@pytest.fixture
def minimal_lims_api(config_for_lims_api: dict) -> LimsAPI:
    """Fixture to provide a LimsAPI instance."""
    return LimsAPI(config=config_for_lims_api)


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


def test_get_capture_kit_strict(minimal_lims_api: LimsAPI, mocker: MockerFixture):
    """Test to get the capture kit for a sample in LIMS."""
    # GIVEN a LIMS API

    # GIVEN a sample with a capture kit in LIMS
    lims_sample = create_autospec(Sample, udf={"Bait Set": "valid_capture_kit"})
    mocker.patch.object(entities.Sample, "__new__", return_value=lims_sample)

    # WHEN getting the sample capture kit
    capture_kit = minimal_lims_api.get_capture_kit_strict(lims_id="sample_id")

    # THEN the capture kit is as expected
    assert capture_kit == "valid_capture_kit"


def test_get_capture_kit_strict_no_capture_kit(minimal_lims_api: LimsAPI, mocker: MockerFixture):
    """Test scenario when capture kit is not set for a sample."""
    # GIVEN a LIMS API

    # GIVEN a sample with no capture kit in LIMS
    lims_sample = create_autospec(Sample, udf={"Bait Set": None})
    mocker.patch.object(entities.Sample, "__new__", return_value=lims_sample)
    mocker.patch.object(Lims, "get_artifacts", return_value=[])

    # WHEN getting the sample capture kit
    # THEN a LimsDataError is raised
    with pytest.raises(LimsDataError):
        minimal_lims_api.get_capture_kit_strict(lims_id="sample_id")


def test_get_latest_artifact_from_list(minimal_lims_api: LimsAPI):
    # GIVEN a LIMS API

    # GIVEN a list of artifacts with different creation dates
    artifact_1 = create_autospec(
        Artifact, parent_process=create_autospec(EntityDescriptor, date_run=dt.datetime(2023, 4, 1))
    )
    artifact_2 = create_autospec(
        Artifact, parent_process=create_autospec(EntityDescriptor, date_run=dt.datetime(2023, 5, 1))
    )
    artifact_3 = create_autospec(
        Artifact, parent_process=create_autospec(EntityDescriptor, date_run=dt.datetime(2023, 3, 1))
    )
    artifacts = [artifact_1, artifact_2, artifact_3]

    # WHEN getting the latest artifact from a list of artifacts with different creation dates
    latest_artifact = minimal_lims_api._get_latest_artifact_from_list(artifact_list=artifacts)

    # THEN the artifact with the latest creation date is returned
    assert latest_artifact == artifact_2


@pytest.mark.parametrize(
    "sample_type, step_name",
    [
        ("wgs", "Aliquot samples for WGS v1"),
        ("tgs", "Aliquot samples for enzymatic fragmentation TWIST v2"),
        ("revio", "Normalization of samples for Shearing or Library Prep (Revio) v1"),
    ],
    ids=["WGS sample", "TGS sample", "Revio sample"],
)
def test_get_latest_input_amount_success(
    minimal_lims_api: LimsAPI, sample_type: str, step_name: str, mocker: MockerFixture
):
    """Test to get the latest input amount for a sample."""
    # GIVEN a LIMS API

    # GIVEN an artifact in the LIMS database with the expected input amount for the sample
    udf_key = "Amount needed (ng)"
    amount_in_lims: float = 10.0
    mocked_get_artifacts = mocker.patch.object(
        Lims,
        "get_artifacts",
        return_value=[create_autospec(Artifact, udf={udf_key: amount_in_lims})],
    )

    # WHEN getting the latest input amount
    input_amount = minimal_lims_api.get_latest_input_amount(
        sample_id="sample_id", sample_type=sample_type
    )

    # THEN the LIMS API get_artifacts method is called with the correct parameters
    mocked_get_artifacts.assert_called_once_with(
        process_type=step_name,
        type=LimsArtifactTypes.ANALYTE,
        samplelimsid="sample_id",
    )

    # THEN the input amount is as expected
    assert input_amount == amount_in_lims
