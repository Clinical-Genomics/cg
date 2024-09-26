"""Test Tomte delivery report API."""

from cg.meta.report.tomte import TomteReportAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.report.metadata import TomteSampleMetadataModel
from cg.store.models import Case, Sample


def test_get_sample_metadata(
    report_api_tomte: TomteReportAPI,
    sample_id: str,
    tomte_case_id: str,
    tomte_validated_metrics: dict[str, str],
    tomte_mock_analysis_finish,
):
    """Test Tomte sample metadata extraction."""

    # GIVEN a Tomte case and associated sample
    case: Case = report_api_tomte.status_db.get_case_by_internal_id(internal_id=tomte_case_id)
    sample: Sample = report_api_tomte.status_db.get_sample_by_internal_id(internal_id=sample_id)

    # GIVEN an analysis metadata object
    latest_metadata: NextflowAnalysis = report_api_tomte.analysis_api.get_latest_metadata(
        case_id=tomte_case_id
    )

    # WHEN getting the sample metadata
    sample_metadata: TomteSampleMetadataModel = report_api_tomte.get_sample_metadata(
        case=case, sample=sample, analysis_metadata=latest_metadata
    )

    # THEN the sample metadata should be correctly retrieved and match the expected metrics
    assert sample_metadata.model_dump() == tomte_validated_metrics
