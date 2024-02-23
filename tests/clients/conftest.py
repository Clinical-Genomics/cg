import pytest
from _pytest.fixtures import FixtureRequest

from cg.clients.janus.api import JanusAPIClient
from cg.clients.janus.dto.create_qc_metrics_request import FilePathAndTag, CreateQCMetricsRequest


@pytest.fixture
def janus_config() -> dict:
    return {"janus": {"host": "janus_host"}}


@pytest.fixture
def client(janus_config: dict) -> JanusAPIClient:
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
    return CreateQCMetricsRequest(
        case_id="testcase",
        sample_ids=["test_sample"],
        files=balsamic_files_wgs,
        workflow="balsamic",
        prep_category="wgs",
    )
