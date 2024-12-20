import os
from unittest.mock import Mock
import pytest
from pathlib import Path

from cg.services.deliver_files.file_formatter.files.abstract import FileFormatter
from cg.services.deliver_files.file_formatter.files.mutant_service import (
    MutantFileFormatter,
)
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.deliver_files.file_fetcher.models import (
    CaseFile,
    SampleFile,
)
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile
from cg.services.deliver_files.file_formatter.files.case_service import (
    CaseFileFormatter,
)
from cg.services.deliver_files.file_formatter.files.concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.files.sample_service import (
    SampleFileFormatter,
    FileManager,
)
from cg.services.deliver_files.file_formatter.path_name.flat_structure import (
    FlatStructurePathFormatter,
)
from cg.services.deliver_files.file_formatter.path_name.nested_structure import (
    NestedStructurePathFormatter,
)


@pytest.mark.parametrize(
    "moved_files,expected_formatted_files,file_formatter",
    [
        (
            "expected_moved_analysis_case_delivery_files",
            "expected_formatted_analysis_case_files",
            CaseFileFormatter(
                file_manager=FileManager(), path_name_formatter=NestedStructurePathFormatter()
            ),
        ),
        (
            "expected_moved_analysis_sample_delivery_files",
            "expected_formatted_analysis_sample_files",
            SampleFileFormatter(
                file_manager=FileManager(), path_name_formatter=NestedStructurePathFormatter()
            ),
        ),
        (
            "fastq_concatenation_sample_files",
            "expected_concatenated_fastq_formatted_files",
            SampleFileConcatenationFormatter(
                file_manager=FileManager(),
                path_name_formatter=NestedStructurePathFormatter(),
                concatenation_service=FastqConcatenationService(),
            ),
        ),
        (
            "fastq_concatenation_sample_files_flat",
            "expected_concatenated_fastq_flat_formatted_files",
            SampleFileConcatenationFormatter(
                file_manager=FileManager(),
                path_name_formatter=FlatStructurePathFormatter(),
                concatenation_service=FastqConcatenationService(),
            ),
        ),
    ],
)
def test_file_formatters(
    moved_files: list[CaseFile | SampleFile],
    expected_formatted_files: list[FormattedFile],
    file_formatter: FileFormatter,
    request,
):
    # GIVEN existing case files, a case file formatter and a ticket directory path and a customer inbox
    moved_files: list[CaseFile | SampleFile] = request.getfixturevalue(moved_files)
    expected_formatted_files: list[FormattedFile] = request.getfixturevalue(
        expected_formatted_files
    )
    delivery_path: Path = moved_files[0].file_path.parent

    os.makedirs(delivery_path, exist_ok=True)

    for moved_file in moved_files:
        moved_file.file_path.touch()

    # WHEN formatting the case files
    formatted_files: list[FormattedFile] = file_formatter.format_files(
        moved_files=moved_files,
        delivery_path=delivery_path,
    )

    # THEN the case files should be formatted
    assert formatted_files == expected_formatted_files
    for file in formatted_files:
        assert file.formatted_path.exists()
        assert not file.original_path.exists()


def test_mutant_file_formatter(
    mutant_moved_files: list[SampleFile],
    expected_mutant_formatted_files: list[FormattedFile],
    lims_naming_metadata: str,
):
    # GIVEN existing ticket directory path and a customer inbox
    ticket_dir_path: Path = mutant_moved_files[0].file_path.parent

    os.makedirs(ticket_dir_path, exist_ok=True)

    for moved_file in mutant_moved_files:
        moved_file.file_path.touch()

    lims_mock = Mock()
    lims_mock.get_sample_region_and_lab_code.return_value = lims_naming_metadata
    file_formatter = MutantFileFormatter(
        file_manager=FileManager(),
        file_formatter=SampleFileConcatenationFormatter(
            file_manager=FileManager(),
            path_name_formatter=NestedStructurePathFormatter(),
            concatenation_service=FastqConcatenationService(),
        ),
        lims_api=lims_mock,
    )

    # WHEN formatting the files
    formatted_files: list[FormattedFile] = file_formatter.format_files(
        moved_files=mutant_moved_files,
        delivery_path=ticket_dir_path,
    )

    # THEN the files should be formatted
    assert formatted_files == expected_mutant_formatted_files
    for file in formatted_files:
        assert file.formatted_path.exists()
        assert not file.original_path.exists()


def test_concatenation_sample_name_match():
    # GIVEN a concatenation service and a list of file paths and a sample name that is a number
    sample_name = "12"
    concatentation_formatter = SampleFileConcatenationFormatter(
        file_manager=Mock(),
        path_name_formatter=Mock(),
        concatenation_service=Mock(),
    )
    # GIVEN two sets of file paths that should match and not match the sample name
    should_match_file_paths = [
        Path("path/to/FC_12_L001_R1_001.fastq.gz"),
        Path("path/to/FC_12_L002_R1_001.fastq.gz"),
        Path("path/to/FC_12_L001_R2_001.fastq.gz"),
        Path("path/to/FC_12_L002_R2_001.fastq.gz"),
    ]
    should_not_match_file_paths = [
        Path("path/to/FC_123_L001_R1_001.fastq.gz"),
        Path("path/to/FC_123_L002_R1_001.fastq.gz"),
        Path("path/to/FC_123_L001_R2_001.fastq.gz"),
        Path("path/to/FC_123_L002_R2_001.fastq.gz"),
    ]

    # WHEN checking if the file paths match the sample name

    # THEN the file paths that should match should return True and the file paths that should not match should return False
    for file_path in should_match_file_paths:
        assert (
            concatentation_formatter._has_expected_sample_name_format_match(
                file_path=file_path, sample_name=sample_name
            )
            is True
        )

    for file_path in should_not_match_file_paths:
        assert (
            concatentation_formatter._has_expected_sample_name_format_match(
                file_path=file_path, sample_name=sample_name
            )
            is False
        )
