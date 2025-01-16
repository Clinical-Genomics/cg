from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.cg_config import CGConfig


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
