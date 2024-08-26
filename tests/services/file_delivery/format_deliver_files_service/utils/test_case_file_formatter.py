import os
from pathlib import Path

from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles, CaseFile
from cg.services.file_delivery.file_formatter_service.models import FormattedFile
from cg.services.file_delivery.file_formatter_service.utils.case_file_formatter import (
    CaseFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.utils import create_ticket_dir


def test_case_file_formatter(
    expected_moved_analysis_delivery_files: DeliveryFiles,
    expected_formatted_analysis_case_files: list[FormattedFile],
):
    # GIVEN existing case files, a case file formatter and a ticket directory path and a customer inbox
    case_file_formatter = CaseFileFormatter()
    ticket_dir_path: Path = expected_moved_analysis_delivery_files.case_files[0].file_path.parent
    os.makedirs(ticket_dir_path, exist_ok=True)
    case_files: list[CaseFile] = expected_moved_analysis_delivery_files.case_files
    for case_file in case_files:
        case_file.file_path.touch()

    # WHEN formatting the case files
    formatted_files: list[FormattedFile] = case_file_formatter.format_files(
        case_files=case_files,
        ticket_dir_path=ticket_dir_path,
    )

    # THEN the case files should be formatted
    assert formatted_files == expected_formatted_analysis_case_files
    for file in formatted_files:
        assert file.formatted_path.exists()
        assert not file.original_path.exists()
