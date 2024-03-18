from http import HTTPStatus

import pytest
from _pytest.fixtures import FixtureRequest
from pytest_mock import MockFixture

from cg.clients.janus.api import JanusAPIClient
from cg.clients.janus.dto.create_qc_metrics_request import (
    CreateQCMetricsRequest,
    FilePathAndTag,
    WorkflowInfo,
)
from cg.constants import PrepCategory, Workflow


@pytest.fixture
def janus_config() -> dict:
    return {"janus": {"host": "janus_host"}}


@pytest.fixture
def janus_client(janus_config: dict) -> JanusAPIClient:
    return JanusAPIClient(janus_config)


@pytest.fixture
def balsamic_files_wgs(request: FixtureRequest) -> list[FilePathAndTag]:
    file_path_tags: dict = {
        "alignment_summary_metrics_path": "picard_alignment_summary_tag",
        "picard_hs_metrics_path": "picard_hs_metrics_tag",
        "picard_dups_path": "picard_dups_tag",
        "picard_wgs_metrics_path": "picard_wgs_metrics_tag",
        "picard_insert_size_path": "picard_insert_size_tag",
        "somalier_path": "somalier_tag",
        "fastp_path": "fastp_tag",
        "samtools_stats_path": "samtools_stats_tag",
    }

    files: list[FilePathAndTag] = []
    for key, value in file_path_tags.items():
        files.append(FilePathAndTag(file_path=str(key), tag=value))
    return files


@pytest.fixture
def collect_qc_request_balsamic_wgs(
    balsamic_files_wgs: list[FilePathAndTag],
) -> CreateQCMetricsRequest:
    workflow_info = WorkflowInfo(workflow=Workflow.BALSAMIC, version="1")
    return CreateQCMetricsRequest(
        case_id="testcase",
        sample_ids=["test_sample"],
        files=balsamic_files_wgs,
        workflow_info=workflow_info,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
    )


@pytest.fixture
def janus_response() -> dict:
    return {"some": "data"}


@pytest.fixture
def mock_post_request_ok(janus_response: dict, mocker: MockFixture) -> MockFixture:
    mocked_response = mocker.Mock()
    mocked_response.status_code = HTTPStatus.OK
    mocked_response.json.return_value = janus_response
    mocked_response.verify = False
    return mocked_response


@pytest.fixture
def mock_post_request_not_found(janus_response: dict, mocker: MockFixture) -> MockFixture:
    mocked_response = mocker.Mock()
    mocked_response.status_code = HTTPStatus.NOT_FOUND
    mocked_response.json.return_value = janus_response
    return mocked_response
