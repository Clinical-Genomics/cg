from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.file_formatter_service.generic_delivery_file_formatter_service import (
    GenericDeliveryFileFormatter,
)
import pytest

from cg.services.file_delivery.file_formatter_service.models import FormattedFiles


@pytest.mark.parametrize(
    "delivery_files,expected_formatted_files,formatter_service",
    [
        "moved_fastq_delivery_files",
        "expected_formatted_fastq_files",
        GenericDeliveryFileFormatter(),
    ],
)
def test_reformat_files(
    delivery_files: DeliveryFiles,
    expected_formatted_files: FormattedFiles,
    formatter_service: DeliveryFileFormattingService,
):
    # GIVEN a delivery file formatter and moved delivery files

    # WHEN reformatting the delivery files
    formatted_files: FormattedFiles = formatter_service.format_files(delivery_files)
    # THEN the delivery files should be reformatted

    assert formatted_files == expected_formatted_files
