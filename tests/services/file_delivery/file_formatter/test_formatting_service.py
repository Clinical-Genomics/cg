from pathlib import Path

import mock

from cg.services.deliver_files.file_fetcher.models import (
    DeliveryFiles,
    SampleFile,
    CaseFile,
    DeliveryMetaData,
)
from cg.services.deliver_files.file_formatter.abstract import (
    DeliveryFileFormattingService,
)
import pytest

from cg.services.deliver_files.file_formatter.models import (
    FormattedFiles,
    FormattedFile,
)


@pytest.mark.parametrize(
    "formatter_service, formatted_case_files, formatted_sample_files, case_files, sample_files",
    [
        (
            "generic_delivery_file_formatter",
            "empty_case_files",
            "expected_formatted_analysis_sample_files",
            "empty_case_files",
            "expected_moved_analysis_sample_delivery_files",
        ),
        (
            "generic_delivery_file_formatter",
            "expected_formatted_analysis_case_files",
            "expected_formatted_analysis_sample_files",
            "expected_moved_analysis_case_delivery_files",
            "expected_moved_analysis_sample_delivery_files",
        ),
    ],
)
def test_reformat_files(
    formatter_service: DeliveryFileFormattingService,
    formatted_case_files: list[FormattedFile],
    formatted_sample_files: list[FormattedFile],
    case_files: list[CaseFile],
    sample_files: list[SampleFile],
    tmp_path: Path,
    request,
):
    # GIVEN a delivery file formatter, mocked delivery files and expected formatted files
    formatter_service = request.getfixturevalue(formatter_service)
    formatted_case_files = request.getfixturevalue(formatted_case_files)
    formatted_sample_files = request.getfixturevalue(formatted_sample_files)
    case_files = request.getfixturevalue(case_files)
    sample_files = request.getfixturevalue(sample_files)

    delivery_data = DeliveryMetaData(
        case_id="some_case",
        customer_internal_id="cust_id",
        ticket_id="ticket_id",
        customer_ticket_inbox=Path(tmp_path, "cust_id", "inbox"),
    )
    mock_delivery_files = DeliveryFiles(
        delivery_data=delivery_data, case_files=case_files, sample_files=sample_files
    )
    files = []
    files.extend(formatted_sample_files)
    if case_files:
        files.extend(formatted_case_files)

    expected_formatted_files = FormattedFiles(files=files)
    with mock.patch(
        "cg.services.deliver_files.file_formatter.utils.sample_service.SampleFileFormatter.format_files",
        return_value=formatted_sample_files,
    ), mock.patch(
        "cg.services.deliver_files.file_formatter.utils.case_service.CaseFileFormatter.format_files",
        return_value=formatted_case_files,
    ):
        # WHEN reformatting the delivery files
        formatted_files: FormattedFiles = formatter_service.format_files(mock_delivery_files)

    # THEN the delivery files should be reformatted
    assert formatted_files == expected_formatted_files
