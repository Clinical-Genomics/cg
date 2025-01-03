import pytest

from cg.models.orders.constants import OrderType
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.store_order_services.store_case_order import StoreCaseOrderService
from cg.services.orders.store_order_services.store_fastq_order_service import StoreFastqOrderService
from cg.services.orders.store_order_services.store_metagenome_order import (
    StoreMetagenomeOrderService,
)
from cg.services.orders.store_order_services.store_microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)
from cg.services.orders.store_order_services.store_microbial_order import StoreMicrobialOrderService
from cg.services.orders.store_order_services.store_pacbio_order_service import (
    StorePacBioOrderService,
)
from cg.services.orders.store_order_services.store_pool_order import StorePoolOrderService
from cg.store.models import Application
from cg.store.store import Store
from tests.mocks.limsmock import MockLimsAPI
from tests.store_helpers import StoreHelpers


@pytest.fixture
def store_generic_order_service(base_store: Store, lims_api: MockLimsAPI) -> StoreCaseOrderService:
    return StoreCaseOrderService(status_db=base_store, lims_service=OrderLimsService(lims_api))


@pytest.fixture
def store_pool_order_service(base_store: Store, lims_api: MockLimsAPI) -> StorePoolOrderService:
    return StorePoolOrderService(status_db=base_store, lims_service=OrderLimsService(lims_api))


@pytest.fixture
def store_fastq_order_service(base_store: Store, lims_api: MockLimsAPI) -> StoreFastqOrderService:
    return StoreFastqOrderService(status_db=base_store, lims_service=OrderLimsService(lims_api))


@pytest.fixture
def store_pacbio_order_service(base_store: Store, lims_api: MockLimsAPI) -> StorePacBioOrderService:
    return StorePacBioOrderService(status_db=base_store, lims_service=OrderLimsService(lims_api))


@pytest.fixture
def store_metagenome_order_service(
    base_store: Store, lims_api: MockLimsAPI, helpers: StoreHelpers
) -> StoreMetagenomeOrderService:
    metagenome_application: Application = helpers.ensure_application_version(
        store=base_store, application_tag="METPCFR030"
    ).application
    metagenome_application.order_types = [OrderType.METAGENOME]
    metagenome_application: Application = helpers.ensure_application_version(
        store=base_store, application_tag="METWPFR030"
    ).application
    metagenome_application.order_types = [OrderType.METAGENOME]
    customer = base_store.get_customer_by_internal_id("cust000")
    helpers.ensure_user(store=base_store, customer=customer)
    return StoreMetagenomeOrderService(
        status_db=base_store, lims_service=OrderLimsService(lims_api)
    )


@pytest.fixture
def store_microbial_order_service(
    base_store: Store, lims_api: MockLimsAPI
) -> StoreMicrobialOrderService:
    return StoreMicrobialOrderService(status_db=base_store, lims_service=OrderLimsService(lims_api))


@pytest.fixture
def store_microbial_fastq_order_service(
    base_store: Store, lims_api: MockLimsAPI
) -> StoreMicrobialFastqOrderService:
    return StoreMicrobialFastqOrderService(
        status_db=base_store, lims_service=OrderLimsService(lims_api)
    )
