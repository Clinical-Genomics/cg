"""Test module for the Rnafusion delivery report API."""

from cg.meta.report.rnafusion import RnafusionReportAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.report.metadata import RnafusionSampleMetadataModel
from cg.store.models import Case, Sample


def test_get_sample_metadata(
    report_api_rnafusion: RnafusionReportAPI,
    sample_id: str,
    rnafusion_case_id: str,
    rnafusion_validated_metrics: dict[str, str],
    rnafusion_mock_analysis_finish,
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
