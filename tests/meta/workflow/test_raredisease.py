"""Module for Rnafusion analysis API tests."""

from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.constants import EXIT_SUCCESS

def test_get_sample_sheet_content(
    raredisease_context: CGConfig,
    raredisease_case_id: str,
):
    """Test Raredisease nextflow sample sheet creation."""

    # GIVEN Raredisease analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    #WHEN getting the sample sheet content
    result = analysis_api.get_sample_sheet_content(case_id = raredisease_case_id)


    # THEN the process should exit successfully
    assert result == ["raredisease_case_enough_reads","nbasdfas"]

