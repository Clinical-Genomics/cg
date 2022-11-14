"""Fixtures for meta/upload tests."""

from datetime import datetime
from pathlib import Path
from typing import Dict

import pytest

from cg.apps.coverage.api import ChanjoAPI
from cg.constants import Pipeline
from cg.constants.tags import HkMipAnalysisTag
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.store import Store, models
from tests.mocks.hk_mock import MockHousekeeperAPI


class MockCoverage(ChanjoAPI):
    """Mock chanjo coverage api."""


@pytest.fixture(name="upload_genotypes_hk_bundle")
def fixture_upload_genotypes_hk_bundle(
    case_id: str, timestamp, case_qc_metrics_deliverables: Path, bcf_file: Path
) -> dict:
    """Returns a dictionary in Housekeeper format with files used in upload Genotype process."""
    data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(case_qc_metrics_deliverables),
                "archive": False,
                "tags": HkMipAnalysisTag.QC_METRICS,
            },
            {"path": str(bcf_file), "archive": False, "tags": ["snv-gbcf", "genotype"]},
        ],
    }
    return data


@pytest.fixture(name="analysis_obj")
def fixture_analysis_obj(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers
) -> models.Analysis:
    """Return a analysis object with a trio."""
    case_obj = analysis_store_trio.family(case_id)
    helpers.add_analysis(store=analysis_store_trio, case=case_obj, started_at=timestamp)
    return analysis_store_trio.family(case_id).analyses[0]


@pytest.fixture(name="upload_genotypes_api")
def fixture_upload_genotypes_api(
    real_housekeeper_api, genotype_api, upload_genotypes_hk_bundle, helpers
) -> UploadGenotypesAPI:
    """Create a upload genotypes api."""
    helpers.ensure_hk_bundle(real_housekeeper_api, upload_genotypes_hk_bundle, include=True)
    _api = UploadGenotypesAPI(
        hk_api=real_housekeeper_api,
        gt_api=genotype_api,
    )

    return _api


@pytest.yield_fixture(scope="function")
def coverage_upload_api(
    chanjo_config: Dict[str, Dict[str, str]], populated_housekeeper_api: MockHousekeeperAPI
):
    """Return a upload coverage API."""
    return UploadCoverageApi(
        status_api=None, hk_api=populated_housekeeper_api, chanjo_api=MockCoverage(chanjo_config)
    )


@pytest.fixture(scope="function")
def analysis(analysis_store, case_id, timestamp):
    """Fixture to mock an analysis."""
    _analysis = analysis_store.add_analysis(pipeline=Pipeline.BALSAMIC, version="version")
    _analysis.family = analysis_store.family(case_id)
    _analysis.config_path = "dummy_path"
    _analysis.completed_at = timestamp
    yield _analysis


@pytest.fixture(name="genotype_analysis_sex")
def fixture_genotype_analysis_sex() -> dict:
    """Return predicted sex per sample_id."""
    return {"ADM1": "male", "ADM2": "male", "ADM3": "female"}
