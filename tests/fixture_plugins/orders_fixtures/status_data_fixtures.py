import pytest

from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
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


@pytest.fixture
def balsamic_status_data(
    balsamic_order_to_submit: dict, store_generic_order_service: StoreCaseOrderService
) -> dict:
    """Parse balsamic order example."""
    project: OrderType = OrderType.BALSAMIC
    order: OrderIn = OrderIn.parse_obj(obj=balsamic_order_to_submit, project=project)
    return store_generic_order_service.order_to_status(order=order)


@pytest.fixture
def fastq_status_data(
    fastq_order_to_submit, store_fastq_order_service: StoreFastqOrderService
) -> dict:
    """Parse fastq order example."""
    project: OrderType = OrderType.FASTQ
    order: OrderIn = OrderIn.parse_obj(obj=fastq_order_to_submit, project=project)
    return store_fastq_order_service.order_to_status(order=order)


@pytest.fixture
def pacbio_status_data(
    pacbio_order_to_submit: dict, store_pacbio_order_service: StorePacBioOrderService
) -> dict:
    """Parse pacbio order example."""
    project: OrderType = OrderType.PACBIO_LONG_READ
    order: OrderIn = OrderIn.parse_obj(obj=pacbio_order_to_submit, project=project)
    return store_pacbio_order_service.order_to_status(order=order)


@pytest.fixture
def metagenome_status_data(
    metagenome_order_to_submit: dict, store_metagenome_order_service: StoreMetagenomeOrderService
) -> dict:
    """Parse metagenome order example."""
    project: OrderType = OrderType.METAGENOME
    order: OrderIn = OrderIn.parse_obj(obj=metagenome_order_to_submit, project=project)

    return store_metagenome_order_service.order_to_status(order=order)


@pytest.fixture
def microbial_status_data(
    microbial_order_to_submit: dict, store_microbial_order_service: StoreMicrobialOrderService
) -> dict:
    """Parse microbial order example."""
    project: OrderType = OrderType.MICROSALT
    order: OrderIn = OrderIn.parse_obj(obj=microbial_order_to_submit, project=project)
    return store_microbial_order_service.order_to_status(order=order)


@pytest.fixture
def microbial_fastq_status_data(
    microbial_fastq_order_to_submit: dict,
    store_microbial_fastq_order_service: StoreMicrobialFastqOrderService,
) -> dict:
    """Parse microbial order example."""
    project: OrderType = OrderType.MICROBIAL_FASTQ
    order: OrderIn = OrderIn.parse_obj(obj=microbial_fastq_order_to_submit, project=project)
    return store_microbial_fastq_order_service.order_to_status(order=order)


@pytest.fixture
def mip_rna_status_data(
    mip_rna_order_to_submit: dict, store_generic_order_service: StoreCaseOrderService
) -> dict:
    """Parse rna order example."""
    project: OrderType = OrderType.MIP_RNA
    order: OrderIn = OrderIn.parse_obj(obj=mip_rna_order_to_submit, project=project)
    return store_generic_order_service.order_to_status(order=order)


@pytest.fixture
def mip_status_data(
    mip_order_to_submit: dict, store_generic_order_service: StoreCaseOrderService
) -> dict:
    """Parse scout order example."""
    project: OrderType = OrderType.MIP_DNA
    order: OrderIn = OrderIn.parse_obj(obj=mip_order_to_submit, project=project)
    return store_generic_order_service.order_to_status(order=order)


@pytest.fixture
def rml_status_data(
    rml_order_to_submit: dict, store_pool_order_service: StorePoolOrderService
) -> dict:
    """Parse rml order example."""
    project: OrderType = OrderType.RML
    order: OrderIn = OrderIn.parse_obj(obj=rml_order_to_submit, project=project)
    return store_pool_order_service.order_to_status(order=order)


@pytest.fixture
def tomte_status_data(
    tomte_order_to_submit: dict, store_generic_order_service: StoreCaseOrderService
) -> dict:
    """Parse TOMTE order example."""
    project: OrderType = OrderType.TOMTE
    order: OrderIn = OrderIn.parse_obj(obj=tomte_order_to_submit, project=project)
    return store_generic_order_service.order_to_status(order=order)
