"""Test module for the Rnafusion delivery report API."""
from typing import Dict

from cg.meta.report.rnafusion import RnafusionReportAPI
from cg.models.report.metadata import RnafusionSampleMetadataModel
from cg.models.rnafusion.rnafusion import RnafusionAnalysis
from cg.store.models import Family, Sample


def test_get_sample_metadata(
    report_api_rnafusion: RnafusionReportAPI,
    rnafusion_sample_id: str,
    case_id: str,
    rnafusion_validated_metrics: Dict[str, str],
    mock_analysis_finish,
):
    """Test Rnafusion sample metadata extraction."""

    # GIVEN a Rnafusion case and associated sample
    case: Family = report_api_rnafusion.status_db.get_case_by_internal_id(
        internal_id=case_id
    )
    sample: Sample = report_api_rnafusion.status_db.get_sample_by_internal_id(
        internal_id=rnafusion_sample_id
    )

    # GIVEN an analysis metadata object
    latest_metadata: RnafusionAnalysis = report_api_rnafusion.analysis_api.get_latest_metadata(
        case_id=case_id
    )

    # WHEN getting the sample metadata
    sample_metadata: RnafusionSampleMetadataModel = report_api_rnafusion.get_sample_metadata(
        case=case, sample=sample, analysis_metadata=latest_metadata
    )

    # THEN the sample metadata should be correctly retrieved and match the expected validated metrics
    assert sample_metadata.dict() == rnafusion_validated_metrics
