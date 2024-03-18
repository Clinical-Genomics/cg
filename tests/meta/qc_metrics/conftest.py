"""Fixtures for the collect qc metrics api."""

from datetime import datetime
from pathlib import Path

import pytest
from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.clients.arnold.api import ArnoldAPIClient
from cg.clients.arnold.dto.create_case_request import CreateCaseRequest
from cg.clients.janus.api import JanusAPIClient
from cg.clients.janus.dto.create_qc_metrics_request import (
    CreateQCMetricsRequest,
    FilePathAndTag,
    WorkflowInfo,
)
from cg.constants.housekeeper_tags import JanusTags
from cg.meta.qc_metrics.collect_qc_metrics import CollectQCMetricsAPI
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def janus_hk_tags() -> list[str]:
    return ["qc-metrics", "janus", "multiqc"]


@pytest.fixture
def file_with_right_tags() -> str:
    return Path("tests", "fixtures", "meta", "qc_metrics", "file_with_right_tags.json").__str__()


@pytest.fixture
def file_without_right_tags() -> str:
    return Path("tests", "fixtures", "meta", "qc_metrics", "file_without_right_tags.json").__str__()


@pytest.fixture(scope="function")
def janus_hk_store(
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    timestamp: datetime,
    case_id_with_single_sample: str,
    file_with_right_tags: str,
    file_without_right_tags: str,
) -> HousekeeperAPI:
    bundle_with_janus_files = {
        "name": case_id_with_single_sample,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": file_with_right_tags,
                "archive": False,
                "tags": ["qc-metrics", "janus", "multiqc", "picard-hs"],
            },
            {
                "path": file_without_right_tags,
                "archive": False,
                "tags": ["not", "the", "tags", "you", "are", "looking", "for"],
            },
        ],
    }
    helpers.ensure_hk_bundle(real_housekeeper_api, bundle_with_janus_files, include=True)
    return real_housekeeper_api


@pytest.fixture(scope="function")
def janus_store(
    store_with_multiple_cases_and_samples: Store, helpers: StoreHelpers, case_id_with_single_sample
) -> Store:
    case: Case = store_with_multiple_cases_and_samples.get_case_by_internal_id(
        case_id_with_single_sample
    )
    helpers.add_analysis(store_with_multiple_cases_and_samples, case=case)
    return store_with_multiple_cases_and_samples


@pytest.fixture
def mock_janus_api() -> JanusAPIClient:
    return JanusAPIClient(config={"janus": {"host": ""}})


@pytest.fixture
def mock_arnold_api() -> ArnoldAPIClient:
    return ArnoldAPIClient(config={"arnold": {"api_url": ""}})


@pytest.fixture(scope="function")
def collect_qc_metrics_api(
    janus_store: Store,
    janus_hk_store: HousekeeperAPI,
    mock_janus_api: JanusAPIClient,
    mock_arnold_api: ArnoldAPIClient,
):
    return CollectQCMetricsAPI(
        hk_api=janus_hk_store,
        status_db=janus_store,
        janus_api=mock_janus_api,
        arnold_api=mock_arnold_api,
    )


@pytest.fixture
def expected_request(
    case_id_with_single_sample: str,
    sample_id_in_single_case: str,
    janus_hk_store: HousekeeperAPI,
    janus_store: Store,
) -> CreateQCMetricsRequest:
    hk_file: File = janus_hk_store.get_files(
        case_id_with_single_sample, tags=JanusTags.tags_to_retrieve
    ).first()
    sample: Sample = janus_store.get_samples_by_case_id(case_id_with_single_sample)[0]
    case: Case = janus_store.get_case_by_internal_id(case_id_with_single_sample)
    file_path_and_tag = FilePathAndTag(file_path=hk_file.full_path, tag="picard-hs")
    return CreateQCMetricsRequest(
        case_id=case_id_with_single_sample,
        sample_ids=[sample.internal_id],
        workflow_info=WorkflowInfo(
            workflow=case.data_analysis, version=case.analyses[0].workflow_version
        ),
        files=[file_path_and_tag],
    )


@pytest.fixture
def mock_case_id() -> str:
    return "mock_id"


@pytest.fixture
def mock_case_qc_metrics(mock_case_id: str) -> dict:
    return {"case_id": mock_case_id, "case_info": {}}


@pytest.fixture
def expected_create_case_request(mock_case_qc_metrics: dict) -> CreateCaseRequest:
    return CreateCaseRequest(**mock_case_qc_metrics)
