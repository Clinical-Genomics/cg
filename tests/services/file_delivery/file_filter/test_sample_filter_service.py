from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_filter.sample_service import SampleFileFilter


def test_filter_delivery_files(expected_fastq_delivery_files: DeliveryFiles, sample_id: str):
    """Test to filter delivery files."""

    # GIVEN a delivery files object with multiple sample ids and a filter delivery files service
    filter_service = SampleFileFilter()
    samples_ids: list[str] = [
        sample.sample_id for sample in expected_fastq_delivery_files.sample_files
    ]
    assert len(set(samples_ids)) > 1

    # WHEN filtering the delivery files
    filtered_delivery_files = filter_service.filter_delivery_files(
        expected_fastq_delivery_files, sample_id
    )

    # THEN assert that the delivery files only contains the sample with the given sample id
    for sample_file in filtered_delivery_files.sample_files:
        assert sample_file.sample_id == sample_id
