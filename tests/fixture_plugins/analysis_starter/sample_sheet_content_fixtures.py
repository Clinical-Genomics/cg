from pathlib import Path

import pytest

from cg.models.rnafusion.rnafusion import RnafusionSampleSheetEntry
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.models import (
    RarediseaseSampleSheetHeaders,
)


@pytest.fixture(scope="function")
def raredisease_sample_sheet_expected_content(
    nextflow_sample_id: str,
    father_sample_id: str,
    nextflow_case_id: str,
    fastq_path_1: Path,
    fastq_path_2: Path,
) -> list[list[str]]:
    """Return the expected sample sheet content  for raredisease."""
    headers: list[str] = RarediseaseSampleSheetHeaders.list()
    entry_1: list[str] = [
        nextflow_sample_id,
        1,
        fastq_path_1,
        fastq_path_2,
        1,
        2,
        "",
        "",
        nextflow_case_id,
    ]
    return [headers, entry_1]


@pytest.fixture(scope="function")
def rnafusion_sample_sheet_content_list(
    fastq_path_1: Path,
    fastq_path_2: Path,
    nextflow_sample_id: str,
    strandedness: str,
) -> list[list[str]]:
    """Return the expected sample sheet content  for rnafusion."""
    headers: list[str] = RnafusionSampleSheetEntry.headers()
    row: list[str] = [
        nextflow_sample_id,
        fastq_path_1,
        fastq_path_2,
        strandedness.value,
    ]
    return [headers, row]
