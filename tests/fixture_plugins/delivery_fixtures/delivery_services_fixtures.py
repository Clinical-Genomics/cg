import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_sample_and_case_delivery_file_tags_service import (
    FetchSampleAndCaseDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_file_service.fetch_analysis_files_service import (
    FetchAnalysisDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.fetch_fastq_files_service import (
    FetchFastqDeliveryFilesService,
)
from cg.services.file_delivery.file_formatter_service.delivery_file_formatter import (
    DeliveryFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.case_file_formatter import (
    CaseFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)
from cg.store.store import Store


@pytest.fixture
def fastq_delivery_service(
    delivery_housekeeper_api: HousekeeperAPI,
    delivery_store_microsalt: Store,
) -> FetchFastqDeliveryFilesService:
    """Fixture to get an instance of FetchFastqDeliveryFilesService."""
    tag_service = FetchSampleAndCaseDeliveryFileTagsService()
    return FetchFastqDeliveryFilesService(
        hk_api=delivery_housekeeper_api,
        status_db=delivery_store_microsalt,
        tags_fetcher=tag_service,
    )


@pytest.fixture
def analysis_delivery_service(
    delivery_housekeeper_api: HousekeeperAPI,
    delivery_store_balsamic: Store,
) -> FetchAnalysisDeliveryFilesService:
    """Fixture to get an instance of FetchAnalysisDeliveryFilesService."""
    tag_service = FetchSampleAndCaseDeliveryFileTagsService()
    return FetchAnalysisDeliveryFilesService(
        hk_api=delivery_housekeeper_api,
        status_db=delivery_store_balsamic,
        tags_fetcher=tag_service,
    )


@pytest.fixture
def generic_delivery_file_formatter() -> DeliveryFileFormatter:
    """Fixture to get an instance of GenericDeliveryFileFormatter."""
    return DeliveryFileFormatter(
        sample_file_formatter=SampleFileFormatter(), case_file_formatter=CaseFileFormatter()
    )
