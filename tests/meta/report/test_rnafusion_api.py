"""Test module for the Rnafusion delivery report API."""

import pytest
from pytest_mock import MockFixture

from cg.constants import NA_FIELD, RIN_MAX_THRESHOLD, RIN_MIN_THRESHOLD
from cg.meta.report.rnafusion import RnafusionReportAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.report.metadata import RnafusionSampleMetadataModel
from cg.store.models import Case, Sample
from tests.mocks.limsmock import MockLimsAPI


def test_get_sample_metadata(
    report_api_rnafusion: RnafusionReportAPI,
    sample_id: str,
    rnafusion_case_id: str,
    rnafusion_validated_metrics: dict[str, str],
    rnafusion_mock_analysis_finish: None,
):
    """Test Rnafusion sample metadata extraction."""

    # GIVEN a Rnafusion case and associated sample
    case: Case = report_api_rnafusion.status_db.get_case_by_internal_id(
        internal_id=rnafusion_case_id
    )
    sample: Sample = report_api_rnafusion.status_db.get_sample_by_internal_id(internal_id=sample_id)

    # GIVEN an analysis metadata object
    latest_metadata: NextflowAnalysis = report_api_rnafusion.analysis_api.get_latest_metadata(
        case_id=rnafusion_case_id
    )

    # WHEN getting the sample metadata
    sample_metadata: RnafusionSampleMetadataModel = report_api_rnafusion.get_sample_metadata(
        case=case, sample=sample, analysis_metadata=latest_metadata
    )

    # THEN the sample metadata should be correctly retrieved and match the expected validated metrics
    assert sample_metadata.model_dump() == rnafusion_validated_metrics


@pytest.mark.parametrize(
    "input_rin, expected_rin",
    [
        (RIN_MAX_THRESHOLD, str(float(RIN_MAX_THRESHOLD))),  # Test for a valid integer input
        (RIN_MAX_THRESHOLD + 1, NA_FIELD),  # Test for an integer above the allowed threshold
        (RIN_MIN_THRESHOLD - 1, NA_FIELD),  # Test for an integer below the allowed threshold
        (None, NA_FIELD),  # Test for a None input
    ],
)
def test_ensure_rin_thresholds(
    rnafusion_case_id: str,
    sample_id: str,
    input_rin: int | float,
    expected_rin: str,
    report_api_rnafusion: RnafusionReportAPI,
    rnafusion_mock_analysis_finish: None,
    mocker: MockFixture,
):
    """Test Rnafusion RIN value validation."""

    # GIVEN a Rnafusion case and associated sample
    case: Case = report_api_rnafusion.status_db.get_case_by_internal_id(
        internal_id=rnafusion_case_id
    )
    sample: Sample = report_api_rnafusion.status_db.get_sample_by_internal_id(internal_id=sample_id)

    # GIVEN an analysis metadata object
    latest_metadata: NextflowAnalysis = report_api_rnafusion.analysis_api.get_latest_metadata(
        case_id=rnafusion_case_id
    )

    # GIVEN a specific RIN value
    mocker.patch.object(MockLimsAPI, "get_sample_rin", return_value=input_rin)

    # WHEN getting the sample metadata
    sample_metadata: RnafusionSampleMetadataModel = report_api_rnafusion.get_sample_metadata(
        case=case, sample=sample, analysis_metadata=latest_metadata
    )

    # THEN the sample RIN value should match the expected RIN value
    assert sample_metadata.rin == expected_rin
