"""Fixtures for meta/upload tests"""

from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.coverage.api import ChanjoAPI
from cg.constants import Pipeline
from cg.constants.tags import HkMipAnalysisTag
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.meta.upload.observations import UploadObservationsAPI
from cg.store import Store, models


class MockCoverage(ChanjoAPI):
    """Mock chanjo coverage api"""


class MockLoqusAPI:
    """Mock LoqusAPI class"""

    def __init__(self, analysis_type="wgs"):
        self.analysis_type = analysis_type

    @staticmethod
    def load(*args, **kwargs):
        """Mock load method"""
        _ = args
        _ = kwargs
        return dict(variants=12)

    @staticmethod
    def get_case(*args, **kwargs):
        """Mock get_case method"""
        _ = args
        _ = kwargs
        return {"case_id": "case_id", "_id": "123"}

    @staticmethod
    def get_duplicate(*args, **kwargs):
        """Mock get_duplicate method"""
        _ = args
        _ = kwargs
        return {"case_id": "case_id"}


@pytest.fixture(name="upload_genotypes_hk_bundle")
def fixture_upload_genotypes_hk_bundle(
    case_id: str, timestamp, case_qc_metrics_deliverables: Path, bcf_file: Path
) -> dict:
    """Returns a dictionary in hk format with files used in upload gt process"""
    data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(case_qc_metrics_deliverables),
                "archive": False,
                "tags": [HkMipAnalysisTag.QC_METRICS],
            },
            {"path": str(bcf_file), "archive": False, "tags": ["snv-gbcf"]},
        ],
    }
    return data


@pytest.fixture(name="analysis_obj")
def fixture_analysis_obj(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers
) -> models.Analysis:
    """Return a analysis object with a trio"""
    case_obj = analysis_store_trio.family(case_id)
    helpers.add_analysis(store=analysis_store_trio, case=case_obj, started_at=timestamp)
    return analysis_store_trio.family(case_id).analyses[0]


@pytest.fixture(name="upload_genotypes_api")
def fixture_upload_genotypes_api(
    real_housekeeper_api, genotype_api, upload_genotypes_hk_bundle, helpers
) -> UploadGenotypesAPI:
    """Create a upload genotypes api"""
    helpers.ensure_hk_bundle(real_housekeeper_api, upload_genotypes_hk_bundle, include=True)
    _api = UploadGenotypesAPI(
        hk_api=real_housekeeper_api,
        gt_api=genotype_api,
    )

    return _api


@pytest.fixture(scope="function")
def upload_observations_api(analysis_store, populated_housekeeper_api):
    """Create mocked UploadObservationsAPI object"""

    loqus_mock = MockLoqusAPI()

    _api = UploadObservationsAPI(
        status_api=analysis_store,
        hk_api=populated_housekeeper_api,
        loqus_api=loqus_mock,
    )

    yield _api


@pytest.fixture(scope="function")
def upload_observations_api_wes(analysis_store, populated_housekeeper_api):
    """Create mocked UploadObservationsAPI object"""

    loqus_mock = MockLoqusAPI(analysis_type="wes")

    _api = UploadObservationsAPI(
        status_api=analysis_store,
        hk_api=populated_housekeeper_api,
        loqus_api=loqus_mock,
    )

    yield _api


@pytest.yield_fixture(scope="function")
def coverage_upload_api(chanjo_config_dict, populated_housekeeper_api):
    """Fixture for coverage upload API"""
    hk_api = populated_housekeeper_api
    status_api = None
    coverage_api = MockCoverage(chanjo_config_dict)
    _api = UploadCoverageApi(status_api=status_api, hk_api=hk_api, chanjo_api=coverage_api)
    return _api


@pytest.fixture(scope="function")
def analysis(analysis_store, case_id, timestamp):
    """Fixture to mock an analysis"""
    _analysis = analysis_store.add_analysis(pipeline=Pipeline.BALSAMIC, version="version")
    _analysis.family = analysis_store.family(case_id)
    _analysis.config_path = "dummy_path"
    _analysis.completed_at = timestamp
    yield _analysis


@pytest.fixture(name="genotype_analysis_sex")
def fixture_genotype_analysis_sex() -> dict:
    """Return predicted sex per sample_id"""
    return {"ADM1": "male", "ADM2": "male", "ADM3": "female"}
