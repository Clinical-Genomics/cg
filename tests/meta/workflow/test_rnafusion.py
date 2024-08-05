"""Module for Rnafusion analysis API tests."""

from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase


def test_parse_analysis(
    rnafusion_context: CGConfig,
    rnafusion_case_id: str,
    sample_id: str,
    rnafusion_multiqc_json_metrics: dict,
    rnafusion_metrics: dict,
    rnafusion_mock_analysis_finish,
):
    """Test Rnafusion output analysis files parsing."""

    # GIVEN a Rnafusion analysis API and a list of QC metrics
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]
    qc_metrics: list[MetricsBase] = analysis_api.get_multiqc_json_metrics(case_id=rnafusion_case_id)

    # WHEN extracting the analysis model
    analysis_model: NextflowAnalysis = analysis_api.parse_analysis(qc_metrics_raw=qc_metrics)

    # THEN the analysis model and its content should have been correctly extracted
    assert analysis_model.sample_metrics[sample_id] == rnafusion_metrics


def test_get_latest_metadata(
    rnafusion_context: CGConfig, rnafusion_case_id: str, rnafusion_mock_analysis_finish
):
    """Test retrieval of Rnafusion latest metadata."""

    # GIVEN a Rnafusion analysis API and a list of QC metrics
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]

    # WHEN collecting the latest metadata
    latest_metadata: NextflowAnalysis = analysis_api.get_latest_metadata(case_id=rnafusion_case_id)

    # THEN the latest metadata should have been parsed
    assert latest_metadata
    assert latest_metadata.sample_metrics
