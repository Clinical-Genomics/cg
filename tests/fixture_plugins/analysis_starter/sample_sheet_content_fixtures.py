from pathlib import Path

import pytest

from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    HEADERS as raredisease_headers,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    HEADERS as rnafusion_headers,
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
    entry_1: list[str] = [
        nextflow_sample_id,
        1,
        fastq_path_1.as_posix(),
        fastq_path_2.as_posix(),
        "1",
        "2",
        "",
        "",
        nextflow_case_id,
    ]
    return [raredisease_headers, entry_1]


@pytest.fixture(scope="function")
def rnafusion_sample_sheet_content_list(
    fastq_path_1: Path,
    fastq_path_2: Path,
    nextflow_sample_id: str,
    strandedness: str,
) -> list[list[str]]:
    """Return the expected sample sheet content  for rnafusion."""
    row: list[str] = [
        nextflow_sample_id,
        fastq_path_1.as_posix(),
        fastq_path_2.as_posix(),
        strandedness.value,
    ]
    return [rnafusion_headers, row]
