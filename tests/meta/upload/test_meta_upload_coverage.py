"""Tests for coverage meta API"""

from datetime import datetime

from cg.apps.coverage.api import ChanjoAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.upload.coverage import UploadCoverageApi
from cg.store.models import Case
from cg.store.store import Store


class MockAnalysis:
    """Mock Analysis object"""

    def __init__(self, case_obj: Case, started_at: datetime):
        self.case_obj = case_obj
        self.case = case_obj
        self.started_at = started_at

    @property
    def family(self):
        """mock case"""
        return self.case_obj


def test_data(
    coverage_upload_api: UploadCoverageApi,
    analysis_store: Store,
    case_id: str,
    timestamp_yesterday: datetime,
):
    """test getting data for chanjo"""
    # GIVEN a coverage api and an analysis object
    coverage_api = coverage_upload_api
    case_name = case_id
    case_obj = analysis_store.get_case_by_internal_id(internal_id=case_name)
    analysis_obj = MockAnalysis(case_obj=case_obj, started_at=timestamp_yesterday)

    # WHEN using the data method
    results = coverage_api.data(analysis_obj=analysis_obj)

    # THEN this returns the data needed to upload samples to chanjo
    assert results["family"] == case_name
    for sample in results["samples"]:
        assert set(sample.keys()) == set(["coverage", "sample", "sample_name"])


def test_upload(
    chanjo_config: dict,
    populated_housekeeper_api: HousekeeperAPI,
    analysis_store: Store,
    mocker,
    case_id: str,
    timestamp_yesterday: datetime,
):
    """test uploading with chanjo."""
    # GIVEN a coverage api and a data dictionary
    mock_upload = mocker.patch.object(ChanjoAPI, "upload")
    mock_sample = mocker.patch.object(ChanjoAPI, "sample")
    mocker.patch.object(ChanjoAPI, "delete_sample")
    hk_api = populated_housekeeper_api
    chanjo_api = ChanjoAPI(config=chanjo_config)
    coverage_api = UploadCoverageApi(status_api=None, hk_api=hk_api, chanjo_api=chanjo_api)
    family_name = case_id
    case_obj = analysis_store.get_case_by_internal_id(family_name)
    analysis_obj = MockAnalysis(case_obj=case_obj, started_at=timestamp_yesterday)
    data = coverage_api.data(analysis_obj=analysis_obj)

    # WHEN uploading samples in data dictionary
    coverage_api.upload(data=data)

    # THEN methods sample, and upload should each have been called three times
    assert mock_upload.call_count == len(data["samples"])
    assert mock_sample.call_count == len(data["samples"])
