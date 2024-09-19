from cg.apps.lims import LimsAPI
from cg.models.orders.constants import OrderType
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.store_order_services.store_case_order import (
    StoreCaseOrderService,
)
from cg.services.orders.store_order_services.store_fastq_order_service import (
    StoreFastqOrderService,
)
from cg.services.orders.store_order_services.store_metagenome_order import (
    StoreMetagenomeOrderService,
)
from cg.services.orders.store_order_services.store_microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)
from cg.services.orders.store_order_services.store_microbial_order import (
    StoreMicrobialOrderService,
)
from cg.services.orders.store_order_services.store_pacbio_order_service import (
    StorePacBioOrderService,
)
from cg.services.orders.store_order_services.store_pool_order import (
    StorePoolOrderService,
)
from cg.services.orders.submitters.case_order_submitter import CaseOrderSubmitter
from cg.services.orders.submitters.fastq_order_submitter import FastqOrderSubmitter
from cg.services.orders.submitters.metagenome_order_submitter import (
    MetagenomeOrderSubmitter,
)
from cg.services.orders.submitters.microbial_order_submitter import (
    MicrobialOrderSubmitter,
)
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.submitters.pacbio_order_submitter import PacbioOrderSubmitter
from cg.services.orders.submitters.pool_order_submitter import PoolOrderSubmitter
from cg.services.orders.validate_order_services.validate_case_order import (
    ValidateCaseOrderService,
)
from cg.services.orders.validate_order_services.validate_fastq_order import (
    ValidateFastqOrderService,
)
from cg.services.orders.validate_order_services.validate_metagenome_order import (
    ValidateMetagenomeOrderService,
)
from cg.services.orders.validate_order_services.validate_microbial_order import (
    ValidateMicrobialOrderService,
)
from cg.services.orders.validate_order_services.validate_pacbio_order import (
    ValidatePacbioOrderService,
)
from cg.services.orders.validate_order_services.validate_pool_order import (
    ValidatePoolOrderService,
)
from cg.store.store import Store


class OrderSubmitterRegistry:
    """
    A registry for OrderSubmitter instances, keyed by OrderType.
    """

    def __init__(self):
        self._registry = {}

    def register(self, order_type: OrderType, order_submitter: OrderSubmitter):
        """Register an OrderSubmitter instance for a given OrderType."""
        self._registry[order_type] = order_submitter

    def get_order_submitter(self, order_type: OrderType) -> OrderSubmitter:
        """Fetch the registered OrderSubmitter for the given OrderType."""
        if order_submitter := self._registry.get(order_type):
            return order_submitter
        raise ValueError(f"No OrderSubmitter registered for order type: {order_type}")


order_service_mapping = {
    OrderType.BALSAMIC: (
        OrderLimsService,
        ValidateCaseOrderService,
        StoreCaseOrderService,
        CaseOrderSubmitter,
    ),
    OrderType.BALSAMIC_QC: (
        OrderLimsService,
        ValidateCaseOrderService,
        StoreCaseOrderService,
        CaseOrderSubmitter,
    ),
    OrderType.BALSAMIC_UMI: (
        OrderLimsService,
        ValidateCaseOrderService,
        StoreCaseOrderService,
        CaseOrderSubmitter,
    ),
    OrderType.FASTQ: (
        OrderLimsService,
        ValidateFastqOrderService,
        StoreFastqOrderService,
        FastqOrderSubmitter,
    ),
    OrderType.FLUFFY: (
        OrderLimsService,
        ValidatePoolOrderService,
        StorePoolOrderService,
        PoolOrderSubmitter,
    ),
    OrderType.METAGENOME: (
        OrderLimsService,
        ValidateMetagenomeOrderService,
        StoreMetagenomeOrderService,
        MetagenomeOrderSubmitter,
    ),
    OrderType.MICROBIAL_FASTQ: (
        OrderLimsService,
        ValidateMicrobialOrderService,
        StoreMicrobialFastqOrderService,
        MicrobialOrderSubmitter,
    ),
    OrderType.MICROSALT: (
        OrderLimsService,
        ValidateMicrobialOrderService,
        StoreMicrobialOrderService,
        MicrobialOrderSubmitter,
    ),
    OrderType.MIP_DNA: (
        OrderLimsService,
        ValidateCaseOrderService,
        StoreCaseOrderService,
        CaseOrderSubmitter,
    ),
    OrderType.MIP_RNA: (
        OrderLimsService,
        ValidateCaseOrderService,
        StoreCaseOrderService,
        CaseOrderSubmitter,
    ),
    OrderType.PACBIO_LONG_READ: (
        OrderLimsService,
        ValidatePacbioOrderService,
        StorePacBioOrderService,
        PacbioOrderSubmitter,
    ),
    OrderType.RML: (
        OrderLimsService,
        ValidatePoolOrderService,
        StorePoolOrderService,
        PoolOrderSubmitter,
    ),
    OrderType.RNAFUSION: (
        OrderLimsService,
        ValidateCaseOrderService,
        StoreCaseOrderService,
        CaseOrderSubmitter,
    ),
    OrderType.SARS_COV_2: (
        OrderLimsService,
        ValidateMicrobialOrderService,
        StoreMicrobialOrderService,
        MicrobialOrderSubmitter,
    ),
    OrderType.TAXPROFILER: (
        OrderLimsService,
        ValidateMetagenomeOrderService,
        StoreMetagenomeOrderService,
        MetagenomeOrderSubmitter,
    ),
    OrderType.TOMTE: (
        OrderLimsService,
        ValidateCaseOrderService,
        StoreCaseOrderService,
        CaseOrderSubmitter,
    ),
}


def build_submitter(lims: LimsAPI, status_db: Store, order_type: OrderType) -> OrderSubmitter:
    """Build an OrderSubmitter instance for the given OrderType."""
    lims_service, validation_service, store_service, submitter_class = order_service_mapping[
        order_type
    ]
    return submitter_class(
        order_validation_service=validation_service(status_db),
        order_store_service=store_service(status_db, lims_service(lims)),
    )


def setup_order_submitter_registry(lims: LimsAPI, status_db: Store) -> OrderSubmitterRegistry:
    """Set up the OrderSubmitterRegistry with all OrderSubmitter instances."""
    registry = OrderSubmitterRegistry()
    for order_type in order_service_mapping.keys():
        registry.register(
            order_type=order_type,
            order_submitter=build_submitter(lims=lims, status_db=status_db, order_type=order_type),
        )
    return registry
