from cg.apps.lims import LimsAPI
from cg.models.orders.constants import OrderType
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.store_order_services.implementations.store_case_order import (
    StoreCaseOrderService,
)
from cg.services.orders.store_order_services.implementations.store_fastq_order_service import (
    StoreFastqOrderService,
)
from cg.services.orders.store_order_services.implementations.store_metagenome_order import (
    StoreMetagenomeOrderService,
)
from cg.services.orders.store_order_services.implementations.store_microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)
from cg.services.orders.store_order_services.implementations.store_microbial_order import (
    StoreMicrobialOrderService,
)
from cg.services.orders.store_order_services.implementations.store_pacbio_order_service import (
    StorePacBioOrderService,
)
from cg.services.orders.store_order_services.implementations.store_pool_order import (
    StorePoolOrderService,
)
from cg.services.orders.store_order_services.store_order_service import StoreOrderService
from cg.store.store import Store


class StoringServiceRegistry:
    """
    A registry for StoreOrderService instances, keyed by OrderType.
    """

    def __init__(self):
        self._registry = {}

    def register(self, order_type: OrderType, storing_service: StoreOrderService):
        """Register a StoreOrderService instance for a given OrderType."""
        self._registry[order_type] = storing_service

    def get_storing_service(self, order_type: OrderType) -> StoreOrderService:
        """Fetch the registered StoreOrderService for the given OrderType."""
        if storing_service := self._registry.get(order_type):
            return storing_service
        raise ValueError(f"No StoreOrderService registered for order type: {order_type}")


order_service_mapping = {
    OrderType.BALSAMIC: (
        OrderLimsService,
        StoreCaseOrderService,
    ),
    OrderType.BALSAMIC_QC: (
        OrderLimsService,
        StoreCaseOrderService,
    ),
    OrderType.BALSAMIC_UMI: (
        OrderLimsService,
        StoreCaseOrderService,
    ),
    OrderType.FASTQ: (
        OrderLimsService,
        StoreFastqOrderService,
    ),
    OrderType.FLUFFY: (
        OrderLimsService,
        StorePoolOrderService,
    ),
    OrderType.METAGENOME: (
        OrderLimsService,
        StoreMetagenomeOrderService,
    ),
    OrderType.MICROBIAL_FASTQ: (
        OrderLimsService,
        StoreMicrobialFastqOrderService,
    ),
    OrderType.MICROSALT: (
        OrderLimsService,
        StoreMicrobialOrderService,
    ),
    OrderType.MIP_DNA: (
        OrderLimsService,
        StoreCaseOrderService,
    ),
    OrderType.MIP_RNA: (
        OrderLimsService,
        StoreCaseOrderService,
    ),
    OrderType.PACBIO_LONG_READ: (
        OrderLimsService,
        StorePacBioOrderService,
    ),
    OrderType.RML: (
        OrderLimsService,
        StorePoolOrderService,
    ),
    OrderType.RNAFUSION: (
        OrderLimsService,
        StoreCaseOrderService,
    ),
    OrderType.SARS_COV_2: (
        OrderLimsService,
        StoreMicrobialOrderService,
    ),
    OrderType.TAXPROFILER: (
        OrderLimsService,
        StoreMetagenomeOrderService,
    ),
    OrderType.TOMTE: (
        OrderLimsService,
        StoreCaseOrderService,
    ),
}


def build_storing_service(
    lims: LimsAPI, status_db: Store, order_type: OrderType
) -> StoreOrderService:
    """Build a StoreOrderService instance for the given OrderType."""
    lims_service, store_service = order_service_mapping[order_type]
    return store_service(status_db, lims_service(lims))


def setup_storing_service_registry(lims: LimsAPI, status_db: Store) -> StoringServiceRegistry:
    """Set up the StoringServiceRegistry with all StoreOrderService instances."""
    registry = StoringServiceRegistry()
    for order_type in order_service_mapping.keys():
        registry.register(
            order_type=order_type,
            storing_service=build_storing_service(
                lims=lims, status_db=status_db, order_type=order_type
            ),
        )
    return registry
