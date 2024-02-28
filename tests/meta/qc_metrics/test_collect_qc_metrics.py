"""Tests for the collect qc metrics module."""

from housekeeper.store.models import File

from cg.clients.janus.dto.create_qc_metrics_request import (
    CreateQCMetricsRequest,
    FilePathAndTag,
)
from cg.meta.qc_metrics.collect_qc_metrics import CollectQCMetricsAPI
from cg.store.models import Case, Sample


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
    file_with_right_tags,
):
    # GIVEN a collect qc metrics api

    # WHEN creating a qc metrics request for a case id
    qc_metrics_request: CreateQCMetricsRequest = collect_qc_metrics_api.create_qc_metrics_request(
        case_id_with_single_sample
    )

    # THEN a qc metrics request is created
    assert qc_metrics_request
    assert qc_metrics_request.case_id == case_id_with_single_sample
    sample: Sample = collect_qc_metrics_api.status_db.get_samples_by_case_id(
        case_id_with_single_sample
    )[0]
    for sample_id in qc_metrics_request.sample_ids:
        assert sample_id == sample.internal_id
    assert len(qc_metrics_request.files) == 1
    file_path_and_tag: FilePathAndTag = qc_metrics_request.files[0]
    assert file_path_and_tag.tag == "hsmetrics"
    assert qc_metrics_request.prep_category == sample.prep_category
    case: Case = collect_qc_metrics_api.status_db.get_case_by_internal_id(
        case_id_with_single_sample
    )
    assert qc_metrics_request.workflow == case.data_analysis
