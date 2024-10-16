import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.deliver_files.tag_fetcher.bam_service import (
    BamDeliveryTagsFetcher,
)
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.deliver_files.tag_fetcher.sample_and_case_service import (
    SampleAndCaseDeliveryTagsFetcher,
)
from cg.services.deliver_files.file_fetcher.analysis_service import (
    AnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.file_fetcher.raw_data_service import (
    RawDataDeliveryFileFetcher,
)
from cg.services.deliver_files.file_formatter.service import (
    DeliveryFileFormatter,
)
from cg.services.deliver_files.file_formatter.utils.case_service import (
    CaseFileFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_service import (
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
