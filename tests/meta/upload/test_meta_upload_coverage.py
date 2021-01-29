"""Tests for coverage meta API"""

import datetime

from cg.apps.coverage.api import ChanjoAPI
from cg.meta.upload.coverage import UploadCoverageApi


class MockAnalysis:
    """ Mock Analysis object """

    def __init__(self, case_obj):
        self.case_obj = case_obj

    @property
    def started_at(self):
        """ mock started_at date """
        return str(datetime.datetime.today())

    @property
    def family(self):
        """ mock case """
        return self.case_obj


def test_data(coverage_upload_api, analysis_store, case_id):
    """test getting data for chanjo"""
    # GIVEN a coverage api and an analysis object
    coverage_api = coverage_upload_api
    case_name = case_id
    case_obj = analysis_store.family(case_name)
    analysis_obj = MockAnalysis(case_obj=case_obj)

    # WHEN using the data method
    results = coverage_api.data(analysis_obj=analysis_obj)

    # THEN this returns the data needed to upload samples to chanjo
    assert results["family"] == case_name
    for sample in results["samples"]:
        assert set(sample.keys()) == set(["coverage", "sample", "sample_name"])


def test_upload(chanjo_config_dict, populated_housekeeper_api, analysis_store, mocker, case_id):
    """test uploading with chanjo"""
    # GIVEN a coverage api and a data dictionary
    mock_upload = mocker.patch.object(ChanjoAPI, "upload")
    mock_sample = mocker.patch.object(ChanjoAPI, "sample")
    mock_remove = mocker.patch.object(ChanjoAPI, "delete_sample")
    hk_api = populated_housekeeper_api
    chanjo_api = ChanjoAPI(config=chanjo_config_dict)
    coverage_api = UploadCoverageApi(status_api=None, hk_api=hk_api, chanjo_api=chanjo_api)
    family_name = case_id
    case_obj = analysis_store.family(family_name)
    analysis_obj = MockAnalysis(case_obj=case_obj)
    data = coverage_api.data(analysis_obj=analysis_obj)

    # WHEN uploading samples in data dictionary
    coverage_api.upload(data=data, replace=True)

    # THEN methods sample, and upload should each have been called three times
    assert mock_upload.call_count == len(data["samples"])
    assert mock_sample.call_count == len(data["samples"])
