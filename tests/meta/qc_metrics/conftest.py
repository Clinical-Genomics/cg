"""Fixtures for the collect qc metrics api."""

from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.clients.arnold.api import ArnoldAPIClient
from cg.clients.janus.api import JanusAPIClient
from cg.meta.qc_metrics.collect_qc_metrics import CollectQCMetricsAPI
from cg.models.cg_config import CGConfig
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
                "tags": ["qc-metrics", "janus", "multiqc", "hsmetrics"],
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
def janus_store(store_with_multiple_cases_and_samples: Store) -> Store:
    return store_with_multiple_cases_and_samples


@pytest.fixture
def mock_janus_api() -> JanusAPIClient:
    return JanusAPIClient(config={"janus": {"host": ""}})


@pytest.fixture
def mock_arnold_api() -> ArnoldAPIClient:
    return ArnoldAPIClient(config={"api_url": ""})


@pytest.fixture(scope="function")
def janus_context(
    context_config: dict,
    janus_store: Store,
    janus_hk_store: HousekeeperAPI,
    mock_janus_api: JanusAPIClient,
    mock_arnold_api: ArnoldAPIClient,
) -> CGConfig:
    """Return a cg config."""
    cg_config = CGConfig(**context_config)
    cg_config.status_db_ = janus_store
    cg_config.housekeeper_api_ = janus_hk_store
    cg_config.janus_api_ = mock_janus_api
    cg_config.arnold_api_ = mock_arnold_api
    return cg_config


@pytest.fixture(scope="function")
def collect_qc_metrics_api(janus_context):
    return CollectQCMetricsAPI(config=janus_context)
