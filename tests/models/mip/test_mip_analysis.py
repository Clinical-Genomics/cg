from cg.models.mip.mip_analysis import MipAnalysis, parse_mip_analysis


def test_instantiate_mip_analysis(mip_analysis_raw: dict):
    """
    Tests raw mip analysis against a pydantic MipAnalysis
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MipAnalysis object
    mip_analysis_object = MipAnalysis(**mip_analysis_raw)

    # THEN assert that it was successfully created
    assert isinstance(mip_analysis_object, MipAnalysis)


def test_instantiate_parse_mip_analysis(
    mip_analysis_config_dna_raw: dict, mip_metrics_deliverables_raw: dict, sample_info_dna_raw: dict
):
    """
    Tests parse_mip_analysis
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MipAnalysis object
    mip_analysis_object = parse_mip_analysis(
        mip_config_raw=mip_analysis_config_dna_raw,
        qc_metrics_raw=mip_metrics_deliverables_raw,
        sample_info_raw=sample_info_dna_raw,
    )

    # THEN assert that it was successfully created
    assert isinstance(mip_analysis_object, MipAnalysis)
