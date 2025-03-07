from pathlib import Path

import pytest

from cg.services.analysis_starter.configurator.file_creators.sample_sheet.models import (
    RarediseaseSampleSheetHeaders,
)


def get_raredisease_sample_sheet_entry(
    sample_id: str, lane: int, fastq1: Path, fastq2: Path, case_id: str
) -> list[str]:
    return [
        sample_id,
        lane,
        fastq1,
        fastq2,
        2,
        0,
        "",
        "",
        case_id,
    ]


@pytest.fixture(scope="function")
def raredisease_sample_sheet_expected_content(
    sample_id: str,
    father_sample_id: str,
    raredisease_case_id: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
) -> list[list[str]]:
    """Return the expected sample sheet content  for raredisease."""
    headers: list[str] = RarediseaseSampleSheetHeaders.list()
    entry_1: list[str] = get_raredisease_sample_sheet_entry(
        sample_id=sample_id,
        lane=1,
        fastq1=fastq_forward_read_path,
        fastq2=fastq_reverse_read_path,
        case_id=raredisease_case_id,
    )
    entry_2: list[str] = get_raredisease_sample_sheet_entry(
        sample_id=sample_id,
        lane=2,
        fastq1=fastq_forward_read_path,
        fastq2=fastq_reverse_read_path,
        case_id=raredisease_case_id,
    )
    entry_3: list[str] = get_raredisease_sample_sheet_entry(
        sample_id=father_sample_id,
        lane=1,
        fastq1=fastq_forward_read_path,
        fastq2=fastq_reverse_read_path,
        case_id=raredisease_case_id,
    )
    entry_4: list[str] = get_raredisease_sample_sheet_entry(
        sample_id=father_sample_id,
        lane=2,
        fastq1=fastq_forward_read_path,
        fastq2=fastq_reverse_read_path,
        case_id=raredisease_case_id,
    )
    return [headers, entry_1, entry_2, entry_3, entry_4]
