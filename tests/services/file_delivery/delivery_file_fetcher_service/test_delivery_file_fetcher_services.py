import pytest

from cg.services.deliver_files.delivery_file_fetcher_service.delivery_file_fetcher_service import (
    FetchDeliveryFilesService,
)
from cg.services.deliver_files.delivery_file_fetcher_service.models import DeliveryFiles


@pytest.mark.parametrize(
    "expected_delivery_files,delivery_file_service",
    [
        ("expected_fastq_delivery_files", "raw_data_delivery_service"),
        ("expected_analysis_delivery_files", "analysis_delivery_service"),
        ("expected_bam_delivery_files", "bam_data_delivery_service"),
    ],
)
def test_get_files_to_deliver(
    expected_delivery_files: DeliveryFiles,
    delivery_file_service: FetchDeliveryFilesService,
    case_id: str,
    request,
):
    """Test to get the files to deliver from the FetchDeliveryFilesService."""
    # GIVEN a case id, samples that are present in Housekeeper and a delivery service
    delivery_file_service = request.getfixturevalue(delivery_file_service)
    expected_delivery_files = request.getfixturevalue(expected_delivery_files)

    # WHEN getting the files to deliver
    delivery_files: DeliveryFiles = delivery_file_service.get_files_to_deliver(case_id)

    # THEN assert that the files to deliver are fetched
    assert delivery_files == expected_delivery_files
