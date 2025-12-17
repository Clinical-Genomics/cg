from cg.constants import SexOptions
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase


def test_parse_analysis(
    nallo_context: CGConfig,
    nallo_case_id: str,
    sample_id: str,
    nallo_multiqc_json_metrics: dict,
    nallo_mock_analysis_finish,
):
    """Test Nallo output analysis files parsing."""

    # GIVEN a Nallo analysis API and a list of QC metrics
    analysis_api: NalloAnalysisAPI = nallo_context.meta_apis["analysis_api"]
    qc_metrics: list[MetricsBase] = analysis_api.get_multiqc_json_metrics(case_id=nallo_case_id)

    # WHEN extracting the analysis model
    analysis_model: NextflowAnalysis = analysis_api.parse_analysis(qc_metrics)

    # THEN the analysis model and its content should have been correctly extracted
    assert analysis_model.sample_metrics[sample_id].model_dump() == {
        "avg_sequence_length": 12792.931765117017,
        "coverage_bases": 99366056494.0,
        "median_coverage": 33.0,
        "percent_duplicates": 1.7232745723252236,
        "predicted_sex": SexOptions.FEMALE,
    }
