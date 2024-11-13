from cg.services.order_validation_service.models.order_with_samples import (
    OrderWithSamples,
)
from cg.services.order_validation_service.workflows.fluffy.constants import (
    fluffyDeliveryType,
)
from cg.services.order_validation_service.workflows.fluffy.models.sample import (
    fluffySample,
)


class fluffyOrder(OrderWithSamples):
    delivery_type: fluffyDeliveryType
    samples: list[fluffySample]

    @property
    def enumerated_samples(self) -> enumerate[fluffySample]:
        return enumerate(self.samples)
