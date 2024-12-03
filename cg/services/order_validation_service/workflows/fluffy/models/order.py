from cg.services.order_validation_service.models.order_with_samples import (
    OrderWithSamples,
)
from cg.services.order_validation_service.workflows.fluffy.constants import (
    FluffyDeliveryType,
)
from cg.services.order_validation_service.workflows.fluffy.models.sample import (
    FluffySample,
)


class FluffyOrder(OrderWithSamples):
    delivery_type: FluffyDeliveryType
    samples: list[FluffySample]

    @property
    def enumerated_samples(self) -> enumerate[FluffySample]:
        return enumerate(self.samples)
