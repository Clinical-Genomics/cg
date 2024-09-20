import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.deliver_files.delivery_file_tag_fetcher_service.bam_delivery_tags_fetcher import (
    BamDeliveryTagsFetcher,
)
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.deliver_files.delivery_file_tag_fetcher_service.sample_and_case_delivery_tags_fetcher import (
    SampleAndCaseDeliveryTagsFetcher,
)
from cg.services.deliver_files.delivery_file_fetcher_service.analysis_delivery_file_fetcher import (
    AnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.delivery_file_fetcher_service.raw_data_delivery_file_fetcher import (
    RawDataDeliveryFileFetcher,
)
from cg.services.deliver_files.delivery_file_formatter_service.delivery_file_formatter import (
    DeliveryFileFormatter,
)
from cg.services.deliver_files.delivery_file_formatter_service.utils.case_file_formatter import (
    CaseFileFormatter,
)
from cg.services.deliver_files.delivery_file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.delivery_file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)
from cg.store.store import Store


@pytest.fixture
def raw_data_delivery_service(
    delivery_housekeeper_api: HousekeeperAPI,
    delivery_store_microsalt: Store,
) -> RawDataDeliveryFileFetcher:
    """Fixture to get an instance of FetchFastqDeliveryFilesService."""
    tag_service = SampleAndCaseDeliveryTagsFetcher()
    return RawDataDeliveryFileFetcher(
        hk_api=delivery_housekeeper_api,
        status_db=delivery_store_microsalt,
        tags_fetcher=tag_service,
    )


@pytest.fixture
def raw_data_delivery_service_no_housekeeper_bundle(
    real_housekeeper_api: HousekeeperAPI,
    delivery_store_microsalt: Store,
) -> RawDataDeliveryFileFetcher:
    """Fixture to get an instance of FetchFastqDeliveryFilesService."""
    tag_service = SampleAndCaseDeliveryTagsFetcher()
    return RawDataDeliveryFileFetcher(
        hk_api=real_housekeeper_api,
        status_db=delivery_store_microsalt,
        tags_fetcher=tag_service,
    )


@pytest.fixture
def bam_data_delivery_service(
    delivery_housekeeper_api: HousekeeperAPI,
    delivery_store_microsalt: Store,
) -> RawDataDeliveryFileFetcher:
    """Fixture to get an instance of FetchFastqDeliveryFilesService."""
    tag_service = BamDeliveryTagsFetcher()
    return RawDataDeliveryFileFetcher(
        hk_api=delivery_housekeeper_api,
        status_db=delivery_store_microsalt,
        tags_fetcher=tag_service,
    )


@pytest.fixture
def bam_data_delivery_service_no_housekeeper_bundle(
    real_housekeeper_api: HousekeeperAPI,
    delivery_store_microsalt: Store,
) -> RawDataDeliveryFileFetcher:
    """Fixture to get an instance of FetchFastqDeliveryFilesService."""
    tag_service = BamDeliveryTagsFetcher()
    return RawDataDeliveryFileFetcher(
        hk_api=real_housekeeper_api,
        status_db=delivery_store_microsalt,
        tags_fetcher=tag_service,
    )


@pytest.fixture
def analysis_delivery_service(
    delivery_housekeeper_api: HousekeeperAPI,
    delivery_store_balsamic: Store,
) -> AnalysisDeliveryFileFetcher:
    """Fixture to get an instance of FetchAnalysisDeliveryFilesService."""
    tag_service = SampleAndCaseDeliveryTagsFetcher()
    return AnalysisDeliveryFileFetcher(
        hk_api=delivery_housekeeper_api,
        status_db=delivery_store_balsamic,
        tags_fetcher=tag_service,
    )


@pytest.fixture
def analysis_delivery_service_no_housekeeper_bundle(
    real_housekeeper_api: HousekeeperAPI,
    delivery_store_balsamic: Store,
) -> AnalysisDeliveryFileFetcher:
    """Fixture to get an instance of FetchAnalysisDeliveryFilesService."""
    tag_service = SampleAndCaseDeliveryTagsFetcher()
    return AnalysisDeliveryFileFetcher(
        hk_api=real_housekeeper_api,
        status_db=delivery_store_balsamic,
        tags_fetcher=tag_service,
    )


@pytest.fixture
def generic_delivery_file_formatter() -> DeliveryFileFormatter:
    """Fixture to get an instance of GenericDeliveryFileFormatter."""
    return DeliveryFileFormatter(
        sample_file_formatter=SampleFileFormatter(), case_file_formatter=CaseFileFormatter()
    )
