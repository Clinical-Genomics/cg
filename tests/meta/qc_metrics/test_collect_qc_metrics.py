"""Tests for the collect qc metrics module."""

from housekeeper.store.models import File

from cg.clients.arnold.dto.create_case_request import CreateCaseRequest
from cg.clients.janus.dto.create_qc_metrics_request import CreateQCMetricsRequest
from cg.meta.qc_metrics.collect_qc_metrics import CollectQCMetricsAPI


def test_get_qc_metrics_file_paths_for_case(
    case_id_with_single_sample: str,
    collect_qc_metrics_api: CollectQCMetricsAPI,
    janus_hk_tags: list[str],
    file_with_right_tags: str,
):
    # GIVEN a Housekeeper store that contains a case with a qc metrics file

    # WHEN retrieving the files
    files: list[File] = collect_qc_metrics_api.get_qc_metrics_file_paths_for_case(
        case_id_with_single_sample
    )

    # THEN file are returned
    assert files
    assert len(files) == 1


def test_create_qc_metrics_request(
    collect_qc_metrics_api: CollectQCMetricsAPI,
    case_id_with_single_sample: str,
    expected_request: CreateQCMetricsRequest,
):
    # GIVEN a collect qc metrics api

    # WHEN creating a qc metrics request for a case id
    qc_metrics_request: CreateQCMetricsRequest = collect_qc_metrics_api.create_qc_metrics_request(
        case_id_with_single_sample
    )

    # THEN a qc metrics request is created
    assert qc_metrics_request == expected_request


def test_create_case_request(
    collect_qc_metrics_api: CollectQCMetricsAPI,
    mock_case_qc_metrics: dict,
    mock_case_id: str,
    expected_create_case_request: CreateCaseRequest,
    mocker,
):

    # GIVEN a mock case qc metrics
    mocker.patch.object(CollectQCMetricsAPI, "get_case_qc_metrics")
    CollectQCMetricsAPI.get_case_qc_metrics.return_value = mock_case_qc_metrics

    # WHEN creating a case request
    create_case_request: CreateCaseRequest = collect_qc_metrics_api.get_create_case_request(
        mock_case_id
    )

    # THEN a create case request is returned
    assert create_case_request == expected_create_case_request
