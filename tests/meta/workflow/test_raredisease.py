"""Module for Raredisease analysis API tests."""

from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig


def test_get_sample_sheet_content_per_sample(
    raredisease_context: CGConfig,
    rnafusion_case_id: str,
    sample_id: str,
):
    """Test Raredisease output analysis files parsing."""

    # GIVEN a sex string analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # THEN the analysis model and its content should have been correctly extracted
    assert analysis_model.sample_metrics[sample_id] == rnafusion_metrics


def test_get_latest_metadata(
    rnafusion_context: CGConfig, rnafusion_case_id: str, rnafusion_mock_analysis_finish
):
    """Test retrieval of Rnafusion latest metadata."""

    # GIVEN a Rnafusion analysis API and a list of QC metrics
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]

    # WHEN collecting the latest metadata
    latest_metadata: RnafusionAnalysis = analysis_api.get_latest_metadata(case_id=rnafusion_case_id)

    # THEN the latest metadata should have been parsed
    assert latest_metadata
    assert latest_metadata.sample_metrics
