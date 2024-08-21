import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.delivery.fetch_delivery_files_tags.fetch_sample_and_case_delivery_file_tags_service import (
    FetchSampleAndCaseDeliveryFileTagsService,
)
from cg.services.delivery.fetch_file_service.fetch_analysis_files_service import (
    FetchAnalysisDeliveryFilesService,
)
from cg.services.delivery.fetch_file_service.fetch_fastq_files_service import (
    FetchFastqDeliveryFilesService,
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
