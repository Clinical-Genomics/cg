from genologics.lims import Artifact, Sample
from mock import create_autospec
from pytest_mock import MockerFixture

from cg.apps.lims.api import LimsAPI
from cg.models.orders.constants import OrderType
from cg.services.orders.storing.service import StoreOrderService
from cg.services.orders.storing.service_registry import StoringServiceRegistry


def test_queue_samples_in_workflow(
    mocker: MockerFixture, storing_service_registry: StoringServiceRegistry
):
    # GIVEN a storing service
    storing_service: StoreOrderService = storing_service_registry.get_storing_service(
        OrderType.BALSAMIC
    )

    # GIVEN a mock API call for routing LIMS artifacts
    mock_route_artifacts = mocker.patch.object(LimsAPI, "route_artifacts")

    # GIVEN some LIMS samples
    sample_1 = create_autospec(
        Sample,
        udf={"Sequencing Analysis": "apptag1"},
        artifact=create_autospec(Artifact),
    )
    sample_1.name = "sample_1"
    sample_2 = create_autospec(
        Sample,
        udf={"Sequencing Analysis": "apptag2"},
        artifact=create_autospec(Artifact),
    )
    sample_2.name = "sample_2"
    lims_samples = [sample_1, sample_2]

    # GIVEN that the sample apptags correspond to a LIMS workflow ID
    mock_get_id = mocker.patch.object(
        storing_service.status_db, "get_lims_workflow_id_by_application_tag", return_value=1
    )

    # WHEN calling method to store samples in workflow
    storing_service._queue_samples_in_workflow(lims_samples)

    # THEN the LIMS workflow ID is fetched for each apptag
    mock_get_id.assert_any_call("apptag1")
    mock_get_id.assert_any_call("apptag2")
    assert mock_get_id.call_count == 2

    # THEN the workflow router should have been called appropriately
    mock_route_artifacts.assert_called_once_with(
        artifact_list=[s.artifact for s in lims_samples],
        workflow_uri="https://clinical-lims-mock.scilifelab.se/api/v2/configuration/workflows/1",
    )
