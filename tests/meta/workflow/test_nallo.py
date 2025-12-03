from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase


def test_get_sample_sheet_content(
    nallo_context: CGConfig,
    nallo_case_id: str,
):
    """Test Nallo nextflow sample sheet creation."""

    # GIVEN Nallo analysis API
    analysis_api: NalloAnalysisAPI = nallo_context.meta_apis["analysis_api"]

    # WHEN getting the sample sheet content
    result = analysis_api.get_sample_sheet_content(case_id=nallo_case_id)

    # THEN return should contain patterns
    patterns = [
        "ADM1",
        "m00000_000000_000000_s4.hifi_reads.bc2021.bam",
        "nallo_case_two_samples",
    ]

    contains_pattern = any(
        any(any(pattern in sub_element for pattern in patterns) for sub_element in element)
        for element in result
    )
    assert contains_pattern


def test_parse_analysis(
    nallo_context: CGConfig,
    nallo_case_id: str,
    sample_id: str,
    nallo_multiqc_json_metrics: dict,
    rnafusion_metrics: dict,
    nallo_mock_analysis_finish,
):
    """Test Nallo output analysis files parsing."""

    # GIVEN a Nallo analysis API and a list of QC metrics
    analysis_api: NalloAnalysisAPI = nallo_context.meta_apis["analysis_api"]
    qc_metrics: list[MetricsBase] = analysis_api.get_multiqc_json_metrics(case_id=nallo_case_id)

    # WHEN extracting the analysis model
    analysis_model: NextflowAnalysis = analysis_api.parse_analysis(qc_metrics)

    # THEN the analysis model and its content should have been correctly extracted
    assert analysis_model.sample_metrics[sample_id].model_dump() == rnafusion_metrics
