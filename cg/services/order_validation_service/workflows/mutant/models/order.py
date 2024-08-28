from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.mutant.constants import (
    MutantDeliveryType,
)
from cg.services.order_validation_service.workflows.mutant.models.sample import (
    MutantSample,
)


class MutantOrder(Order):
    delivery_type: MutantDeliveryType
    samples: list[MutantSample]
