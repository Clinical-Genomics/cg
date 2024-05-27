"""Module for Raredisease analysis API tests."""

import os

from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig


def test_get_sample_sheet_content(
    raredisease_context: CGConfig,
    raredisease_case_id: str,
):
    """Test Raredisease nextflow sample sheet creation."""

    # GIVEN Raredisease analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # WHEN getting the sample sheet content
    result = analysis_api.get_sample_sheet_content(case_id=raredisease_case_id)

    # THEN return should contain patterns
    patterns = [
        "ADM1",
        "XXXXXXXXX_000000_S000_L001_R1_001.fastq.gz",
        "raredisease_case_enough_reads",
    ]

    contains_pattern = any(
        any(any(pattern in sub_element for pattern in patterns) for sub_element in element)
        for element in result
    )
    assert contains_pattern


def test_write_params_file(raredisease_context: CGConfig, raredisease_case_id: str, mocker):
    # GIVEN Raredisease analysis API and input (nextflow sample sheet path)/output (case directory) parameters
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # WHEN creating case directory
    analysis_api.create_case_directory(case_id=raredisease_case_id, dry_run=False)

    # THEN care directory is created
    assert os.path.exists(analysis_api.get_case_path(case_id=raredisease_case_id))

    mocker.patch.object(RarediseaseAnalysisAPI, "get_target_bed_from_lims")
    RarediseaseAnalysisAPI.get_target_bed_from_lims.return_value = "some_target_bed_file"

    # WHEN writing parameters file
    analysis_api.write_params_file(case_id=raredisease_case_id)

    # THEN the file is created
    assert os.path.isfile(analysis_api.get_params_file_path(case_id=raredisease_case_id))

    # WHEN writing config file
    analysis_api.create_nextflow_config(case_id=raredisease_case_id)

    # THEN the file is created
    assert os.path.isfile(analysis_api.get_nextflow_config_path(case_id=raredisease_case_id))
