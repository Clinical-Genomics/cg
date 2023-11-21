"""Module for Taxprofiler analysis API tests."""


from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase


def test_parse_analysis(
    taxprofiler_context: CGConfig,
    taxprofiler_case_id: str,
    sample_id: str,
    taxprofiler_multiqc_json_metrics: dict,
    taxprofiler_metrics: dict,
    taxprofiler_mock_analysis_finish,
):
    """Test Taxprofiler output analysis files parsing."""

    # GIVEN a Taxprofiler analysis API and a list of QC metrics
    analysis_api: TaxprofilerAnalysisAPI = taxprofiler_context.meta_apis["analysis_api"]
    qc_metrics: list[MetricsBase] = analysis_api.get_multiqc_json_metrics(case_id=taxprofiler_case_id, pipeline_metrics=taxprofiler_multiqc_json_metrics)


    # WHEN extracting the analysis model
  #  analysis_model: TaxprofilerAnalysis = analysis_api.parse_analysis(qc_metrics_raw=qc_metrics)

    # THEN the analysis model and its content should have been correctly extracted
    #assert analysis_model.sample_metrics[sample_id] == rnafusion_metrics
