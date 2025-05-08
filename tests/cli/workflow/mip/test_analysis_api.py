from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI


def test_get_cases_ready_for_analysis(mip_dna_analysis_api: MipDNAAnalysisAPI):

    # GIVEN a balsamic_context with 3 case that is ready for analysis

    # WHEN running the command
    cases_to_analyse = mip_dna_analysis_api.get_cases_ready_for_analysis()

    # THEN only 1 case is retrieved
    assert len(cases_to_analyse) == 3


def test_get_cases_ready_for_analysis_with_limit(mip_dna_analysis_api: MipDNAAnalysisAPI):
    # GIVEN a balsamic_context with 1 case that is ready for analysis

    # WHEN running the command with limit=1
    cases_to_analyse = mip_dna_analysis_api.get_cases_ready_for_analysis(limit=1)

    # THEN no case is retrieved
    assert len(cases_to_analyse) == 1
