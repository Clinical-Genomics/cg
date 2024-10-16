from cg.constants.constants import Workflow
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.mip.mip_analysis import MipAnalysis


def test_instantiate_mip_analysis(mip_analysis_raw: dict):
    """Tests raw mip analysis against a pydantic MipAnalysis."""
    # GIVEN a dictionary with some metrics

    # WHEN instantiating a MipAnalysis object
    mip_dna_analysis = MipAnalysis(**mip_analysis_raw)

    # THEN assert that it was successfully created
    assert isinstance(mip_dna_analysis, MipAnalysis)


def test_instantiate_parse_mip_analysis(
    cg_context,
    mip_analysis_config_dna_raw: dict,
    mip_metrics_deliverables_raw: dict,
    sample_info_dna_raw: dict,
):
    """Tests parse_analysis."""
    # GIVEN a dictionary with some metrics and a MIP analysis API
    mip_analysis_api = MipAnalysisAPI(cg_context, Workflow.MIP_DNA)

    # WHEN instantiating a MipAnalysis object
    mip_dna_analysis = mip_analysis_api.parse_analysis(
        config_raw=mip_analysis_config_dna_raw,
        qc_metrics_raw=mip_metrics_deliverables_raw,
        sample_info_raw=sample_info_dna_raw,
    )

    # THEN assert that it was successfully created
    assert isinstance(mip_dna_analysis, MipAnalysis)
