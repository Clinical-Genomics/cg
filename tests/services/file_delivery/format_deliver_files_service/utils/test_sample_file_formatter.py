import os
from pathlib import Path

from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles, SampleFile
from cg.services.file_delivery.file_formatter_service.models import FormattedFile
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)


def test_sample_file_formatter(
    expected_moved_analysis_delivery_files: DeliveryFiles,
    expected_formatted_analysis_sample_files: list[FormattedFile],
):
    # GIVEN existing case files, a case file formatter and a ticket directory path and a customer inbox
    sample_file_formatter = SampleFileFormatter()
    ticket_dir_path: Path = expected_moved_analysis_delivery_files.sample_files[0].file_path.parent
    os.makedirs(ticket_dir_path, exist_ok=True)
    sample_files: list[SampleFile] = expected_moved_analysis_delivery_files.sample_files
    for sample_file in sample_files:
        sample_file.file_path.touch()

    # WHEN formatting the case files
    formatted_files: list[FormattedFile] = sample_file_formatter.format_files(
        sample_files=sample_files,
        ticket_dir_path=ticket_dir_path,
    )

    # THEN the case files should be formatted
    assert formatted_files == expected_formatted_analysis_sample_files
    for file in formatted_files:
        assert file.formatted_path.exists()
        assert not file.original_path.exists()
