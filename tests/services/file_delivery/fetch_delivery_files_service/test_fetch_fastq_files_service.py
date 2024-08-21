from cg.services.file_delivery.fetch_file_service.fetch_fastq_files_service import (
    FetchFastqDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles


def test_get_files_to_deliver(
    fastq_delivery_service: FetchFastqDeliveryFilesService,
    case_id: str,
    sample_id: str,
    another_sample_id: str,
):
    """Test to get the files to deliver from the FetchFastqDeliverFilesService."""
    # GIVEN a case id, samples that are present in housekeeper and a delivery service
    samples_in_housekeeper: list[str] = [sample_id, another_sample_id]

    # WHEN getting the files to deliver
    delivery_files: DeliveryFiles = fastq_delivery_service.get_files_to_deliver(case_id)

    # THEN assert that the files to deliver are fetched
    assert delivery_files

    # THEN assert that the case files are None
    assert delivery_files.case_files is None

    # THEN assert that all sample fastq files are fetched for the samples present in housekeeper

    # THEN assert that the sample files have the required attributes
    for sample_file in delivery_files.sample_files:
        assert sample_file.sample_id in samples_in_housekeeper
        assert sample_file.file_path
        assert sample_file.case_id == case_id
