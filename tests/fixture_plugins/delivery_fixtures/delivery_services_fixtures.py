import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.deliver_files.tag_fetcher.bam_service import (
    BamDeliveryTagsFetcher,
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
from cg.services.deliver_files.file_formatter.destination.customer_inbox_service import (
    CustomerInboxDeliveryFormatter,
)
from cg.services.deliver_files.file_formatter.component_file.case_service import (
    CaseFileFormatter,
)
from cg.services.deliver_files.file_formatter.component_file.sample_service import (
    SampleFileFormatter,
    FileManager,
)
from cg.services.deliver_files.file_formatter.path_name.nested_structure import (
    NestedStructurePathFormatter,
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
def generic_delivery_file_formatter() -> CustomerInboxDeliveryFormatter:
    """Fixture to get an instance of GenericDeliveryFileFormatter."""
    return CustomerInboxDeliveryFormatter(
        sample_file_formatter=SampleFileFormatter(
            file_manager=FileManager(), file_name_formatter=NestedStructurePathFormatter()
        ),
        case_file_formatter=CaseFileFormatter(
            file_manager=FileManager(),
            path_name_formatter=NestedStructurePathFormatter(),
        ),
    )
