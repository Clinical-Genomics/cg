import pytest

from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile
from cg.services.deliver_files.file_formatter.path_name.flat_structure import (
    FlatStructurePathFormatter,
)
from cg.services.deliver_files.file_formatter.path_name.nested_structure import (
    NestedStructurePathFormatter,
)


@pytest.mark.parametrize(
    "sample_files,expected_formatted_files,path_name_formatter",
    [
        (
            "expected_moved_analysis_sample_delivery_files",
            "expected_formatted_analysis_sample_files",
            NestedStructurePathFormatter(),
        ),
        (
            "expected_moved_analysis_sample_delivery_files",
            "expected_flat_formatted_analysis_sample_files",
            FlatStructurePathFormatter(),
        ),
    ],
)
def test_path_name_formatters(
    sample_files: list[SampleFile],
    expected_formatted_files: list[FormattedFile],
    path_name_formatter,
    request,
):
    # GIVEN existing sample files and a sample file formatter
    sample_files: list[SampleFile] = request.getfixturevalue(sample_files)
    expected_formatted_files: list[FormattedFile] = request.getfixturevalue(
        expected_formatted_files
    )

    # WHEN formatting the sample files
    formatted_files: list[FormattedFile] = [
        FormattedFile(
            formatted_path=path_name_formatter.format_file_path(
                file_path=sample_file.file_path,
                provided_name=sample_file.sample_name,
                provided_id=sample_file.sample_id,
            ),
            original_path=sample_file.file_path,
        )
        for sample_file in sample_files
    ]

    # THEN the sample files should be formatted
    assert formatted_files == expected_formatted_files
