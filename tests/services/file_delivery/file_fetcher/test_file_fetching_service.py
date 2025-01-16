import pytest

from cg.services.deliver_files.file_fetcher.abstract import (
    FetchDeliveryFilesService,
)
from cg.services.deliver_files.file_fetcher.exc import NoDeliveryFilesError
from cg.services.deliver_files.file_fetcher.models import DeliveryFiles


@pytest.mark.parametrize(
    "expected_delivery_files,delivery_file_service,sample_id_to_fetch",
    [
        ("expected_fohm_delivery_files", "fohm_data_delivery_service", "empty_sample"),
        ("expected_fastq_delivery_files", "raw_data_delivery_service", "empty_sample"),
        ("expected_analysis_delivery_files", "analysis_delivery_service", "empty_sample"),
        ("expected_bam_delivery_files", "bam_data_delivery_service", "empty_sample"),
        ("expected_bam_delivery_files_single_sample", "bam_data_delivery_service", "sample_id"),
    ],
)
def test_get_files_to_deliver(
    expected_delivery_files: DeliveryFiles,
    delivery_file_service: FetchDeliveryFilesService,
    sample_id_to_fetch: str | None,
    case_id: str,
    request,
):
    """Test to get the files to deliver from the FetchDeliveryFilesService."""
    # GIVEN a case id, samples that are present in Housekeeper and a delivery service
    delivery_file_service = request.getfixturevalue(delivery_file_service)
    expected_delivery_files = request.getfixturevalue(expected_delivery_files)
    sample_id: str | None = request.getfixturevalue(sample_id_to_fetch)

    # WHEN getting the files to deliver
    delivery_files: DeliveryFiles = delivery_file_service.get_files_to_deliver(
        case_id=case_id, sample_id=sample_id
    )

    # THEN assert that the files to deliver are fetched
    assert delivery_files == expected_delivery_files


@pytest.mark.parametrize(
    "delivery_file_service",
    [
        "raw_data_delivery_service_no_housekeeper_bundle",
        "analysis_delivery_service_no_housekeeper_bundle",
        "bam_data_delivery_service_no_housekeeper_bundle",
    ],
)
def test_get_files_to_deliver_no_files_present(
    delivery_file_service: FetchDeliveryFilesService,
    case_id: str,
    request,
):
    """Test to get the files to deliver from the FetchDeliveryFilesService when no files are present."""

    # GIVEN a case id, samples that are not present in housekeeper and a delivery service
    delivery_file_service = request.getfixturevalue(delivery_file_service)

    # WHEN getting the files to deliver that raises an NoDeliveryFilesError

    # THEN assert that the NoDeliveryFilesError is raised
    with pytest.raises(NoDeliveryFilesError):
        delivery_file_service.get_files_to_deliver(case_id)
