"""Tests for coverage meta API"""

from unittest import mock
from unittest.mock import Mock, create_autospec

from housekeeper.store.models import File
from sqlalchemy.orm import Query

from cg.apps.coverage.api import ChanjoAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.upload.coverage import UploadCoverageApi
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store


def test_data():
    """Test that getting data for coverage upload returns the expected structure."""

    def files(version, tags):
        query = create_autospec(Query)
        if tags == {"sample_id", "chanjo", "sambamba-depth", "coverage"}:
            query.one = Mock(return_value=create_autospec(File, full_path="path/to/coverage/file"))
        else:
            query.one = Mock(side_effect=ValueError("No file found"))
        return query

    # GIVEN a coverage upload API
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.files = Mock(side_effect=files)

    coverage_upload_api = UploadCoverageApi(
        status_api=None, hk_api=housekeeper_api, chanjo_api=Mock()
    )

    # GIVEN an analysis with a case and a sample
    sample: Sample = create_autospec(Sample, internal_id="sample_id")
    sample.name = "sample_name"
    case: Case = create_autospec(Case, internal_id="case_id", samples=[sample])
    case.name = "case_name"
    analysis: Analysis = create_autospec(Analysis, case=case, housekeeper_version_id=1234)

    # WHEN using the data method
    results = coverage_upload_api.data(analysis=analysis)

    # THEN this returns the data needed to upload samples to chanjo
    expected_result = {
        "family": "case_id",
        "family_name": "case_name",
        "samples": [
            {
                "coverage": "path/to/coverage/file",
                "sample": "sample_id",
                "sample_name": "sample_name",
            }
        ],
    }
    assert results == expected_result


def test_upload(
    chanjo_config: dict,
    populated_housekeeper_api: HousekeeperAPI,
    analysis_store: Store,
    mocker,
    case_id: str,
):
    """Test uploading with chanjo."""
    # GIVEN a coverage api
    mock_upload = mocker.patch.object(ChanjoAPI, "upload")
    mock_sample = mocker.patch.object(ChanjoAPI, "sample")
    mocker.patch.object(ChanjoAPI, "delete_sample")
    hk_api = populated_housekeeper_api
    chanjo_api = ChanjoAPI(config=chanjo_config)
    coverage_api = UploadCoverageApi(status_api=None, hk_api=hk_api, chanjo_api=chanjo_api)

    # GIVEN a data dictionary with samples
    case_obj: Case = analysis_store.get_case_by_internal_id(case_id)
    analysis: Analysis = create_autospec(Analysis)
    analysis.case = case_obj
    analysis.housekeeper_version_id = 1234
    with mock.patch.object(HousekeeperAPI, "files") as mock_files:
        mock_files.return_value.first.return_value.full_path = "path/to/coverage/file"
        mock_files.return_value.first.return_value.internal_id = 1
        mock_files.return_value.first.return_value.tags = ["coverage"]
        data = coverage_api.data(analysis=analysis)

    # WHEN uploading samples in data dictionary
    coverage_api.upload(data=data)

    # THEN methods sample, and upload should each have been called three times
    assert mock_upload.call_count == len(data["samples"])
    assert mock_sample.call_count == len(data["samples"])
