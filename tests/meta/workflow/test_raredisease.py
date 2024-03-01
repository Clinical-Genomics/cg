"""Module for Rnafusion analysis API tests."""

from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.constants import EXIT_SUCCESS
from pathlib import Path


def test_get_sample_sheet_content(
    raredisease_context: CGConfig,
    raredisease_case_id: str,
):
    """Test Raredisease nextflow sample sheet creation."""

    # GIVEN Raredisease analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # WHEN getting the sample sheet content
    result = analysis_api.get_sample_sheet_content(case_id=raredisease_case_id)

    expected = [
            [
            "ADM1",
            1,
            Path(
                "/tmp/pytest-of-runner/pytest-0/popen-gw1/housekeeper0/XXXXXXXXX_000000_S000_L001_R1_001.fastq.gz"
            ),
            Path(
                "/tmp/pytest-of-runner/pytest-0/popen-gw1/housekeeper0/XXXXXXXXX_000000_S000_L001_R2_001.fastq.fastq.gz"
            ),
            2,
            <PlinkPhenotypeStatus.UNKNOWN: 0>,
            "",
            "",
            "raredisease_case_enough_reads",
            ],
            [
            "ADM1",
            2,
            Path(
                "/tmp/pytest-of-runner/pytest-0/popen-gw1/housekeeper0/XXXXXXXXX_000000_S000_L001_R1_001.fastq.gz"
            ),
            Path(
                "/tmp/pytest-of-runner/pytest-0/popen-gw1/housekeeper0/XXXXXXXXX_000000_S000_L001_R2_001.fastq.fastq.gz"
            ),
            2,
            <PlinkPhenotypeStatus.UNKNOWN: 0>,
            "",
            "",
            "raredisease_case_enough_reads",
            ]
        ]

    # THEN the process should exit successfully
    assert result == expected
