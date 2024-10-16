import os
import pytest
from pathlib import Path

from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.deliver_files.file_fetcher.models import (
    DeliveryFiles,
    CaseFile,
    SampleFile,
)
from cg.services.deliver_files.file_formatter.models import FormattedFile
from cg.services.deliver_files.file_formatter.utils.case_service import (
    CaseFileFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_service import (
    SampleFileFormatter,
)


@pytest.mark.parametrize(
    "moved_files,expected_formatted_files,file_formatter",
    [
        (
            "expected_moved_analysis_case_delivery_files",
            "expected_formatted_analysis_case_files",
            CaseFileFormatter(),
        ),
        (
            "expected_moved_analysis_sample_delivery_files",
            "expected_formatted_analysis_sample_files",
            SampleFileFormatter(),
        ),
        (
            "fastq_concatenation_sample_files",
            "expected_concatenated_fastq_formatted_files",
            SampleFileConcatenationFormatter(FastqConcatenationService()),
        ),
    ],
)
def test_file_formatter_utils(
    moved_files: list[CaseFile | SampleFile],
    expected_formatted_files: list[FormattedFile],
    file_formatter: CaseFileFormatter | SampleFileFormatter | SampleFileConcatenationFormatter,
    request,
):
    # GIVEN existing case files, a case file formatter and a ticket directory path and a customer inbox
    moved_files: list[CaseFile | SampleFile] = request.getfixturevalue(moved_files)
    expected_formatted_files: list[FormattedFile] = request.getfixturevalue(
        expected_formatted_files
    )
    ticket_dir_path: Path = moved_files[0].file_path.parent

    os.makedirs(ticket_dir_path, exist_ok=True)

    for moved_file in moved_files:
        moved_file.file_path.touch()

    # WHEN formatting the case files
    formatted_files: list[FormattedFile] = file_formatter.format_files(
        moved_files=moved_files,
        ticket_dir_path=ticket_dir_path,
    )

    # THEN the case files should be formatted
    assert formatted_files == expected_formatted_files
    for file in formatted_files:
        assert file.formatted_path.exists()
        assert not file.original_path.exists()
