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
def test_component_formatters(
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
