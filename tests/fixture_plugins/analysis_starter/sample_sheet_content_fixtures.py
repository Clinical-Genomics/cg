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
) -> str:
    """Return the expected sample sheet content  for raredisease."""
    headers: str = ",".join(RarediseaseSampleSheetHeaders.list())
    row: str = ",".join(
        [
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
    )
    return "\n".join([headers, row])
