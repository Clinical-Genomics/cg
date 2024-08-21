from cg.services.file_delivery.fetch_file_service.fetch_fastq_files_service import (
    FetchFastqDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles


def test_get_files_to_deliver(fastq_delivery_service: FetchFastqDeliveryFilesService, case_id: str):
    """Test to get the files to deliver from the FetchFastqDeliverFilesService."""
    # GIVEN a case id and a delivery service

    # WHEN getting the files to deliver
    delivery_files: DeliveryFiles = fastq_delivery_service.get_files_to_deliver(case_id)

    # THEN assert that the files to deliver are fetched
    assert delivery_files
