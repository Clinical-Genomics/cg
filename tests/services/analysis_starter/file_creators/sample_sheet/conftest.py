from pathlib import Path

import pytest

from cg.constants.sequencing import SequencingPlatform
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.nallo import (
    HEADERS as NALLO_HEADERS,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    HEADERS as RAREDISEASE_HEADERS,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    HEADERS as RNAFUSION_HEADERS,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.taxprofiler import (
    HEADERS as TAXPROFILER_HEADERS,
)


@pytest.fixture
def expected_nallo_sample_sheet_content() -> list[list[str]]:
    """Return the expected sample sheet content for Nallo."""
    row1: list[str] = [
        "nallo_case",
        "nallo_sample",
        "/a/path/to/file1.bam",
        "nallo_case",
        "father",
        "mother",
        "1",
        "2",
    ]
    row2: list[str] = [
        "nallo_case",
        "nallo_sample",
        "/a/path/to/file2.bam",
        "nallo_case",
        "father",
        "mother",
        "1",
        "2",
    ]
    return [NALLO_HEADERS, row1, row2]


@pytest.fixture
def raredisease_sample_sheet_expected_content(
    nextflow_sample_id: str,
    father_sample_id: str,
    nextflow_case_id: str,
    fastq_path_1: Path,
    fastq_path_2: Path,
) -> list[list[str]]:
    """Return the expected sample sheet content for raredisease."""
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
    return [RAREDISEASE_HEADERS, entry_1]


@pytest.fixture
def rnafusion_sample_sheet_expected_content(
    fastq_path_1: Path,
    fastq_path_2: Path,
    nextflow_sample_id: str,
    strandedness: str,
) -> list[list[str]]:
    """Return the expected sample sheet content for RNAFUSION."""
    row: list[str] = [
        nextflow_sample_id,
        fastq_path_1.as_posix(),
        fastq_path_2.as_posix(),
        strandedness.value,
    ]
    return [RNAFUSION_HEADERS, row]


@pytest.fixture
def taxprofiler_sample_sheet_expected_content(
    nextflow_sample_id: str,
    nextflow_case_id: str,
    fastq_path_1: Path,
    fastq_path_2: Path,
) -> list[list[str]]:
    """Return the expected sample sheet content for Taxprofiler."""
    row: list[str | int] = [
        nextflow_sample_id,
        1,
        SequencingPlatform.ILLUMINA.value,
        fastq_path_1.as_posix(),
        fastq_path_2.as_posix(),
        "",
    ]
    return [TAXPROFILER_HEADERS, row]
