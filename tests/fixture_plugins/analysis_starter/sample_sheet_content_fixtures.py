from pathlib import Path

import pytest

from cg.services.analysis_starter.configurator.file_creators.sample_sheet.models import (
    RarediseaseSampleSheetHeaders,
)


@pytest.fixture(scope="function")
def raredisease_sample_sheet_content(
    sample_id: str,
    raredisease_case_id: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
) -> list[list[str]]:
    """Return the expected sample sheet content  for raredisease."""
    headers: list[str] = RarediseaseSampleSheetHeaders.list()
    row_link_1: list[str] = [
        sample_id,
        "1",
        fastq_forward_read_path.as_posix(),
        fastq_reverse_read_path.as_posix(),
        "2",
        "0",
        "",
        "",
        raredisease_case_id,
    ]
    row_link_2: list[str] = [
        sample_id,
        "1",
        fastq_forward_read_path.as_posix(),
        fastq_reverse_read_path.as_posix(),
        "2",
        "0",
        "",
        "",
        raredisease_case_id,
    ]
    return [headers, row_link_1, row_link_2]
