from cg.services.order_validation_service.models.order_with_samples import OrderWithNonHumanSamples
from cg.services.order_validation_service.workflows.mutant.constants import (
    MutantDeliveryType,
)
from cg.services.order_validation_service.workflows.mutant.models.sample import (
    MutantSample,
)


class MutantOrder(OrderWithNonHumanSamples):
    delivery_type: MutantDeliveryType
    samples: list[MutantSample]
