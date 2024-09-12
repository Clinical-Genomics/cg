from cg.services.order_validation_service.models.order_with_samples import OrderWithNonHumanSamples
from cg.services.order_validation_service.workflows.microsalt.constants import (
    MicrosaltDeliveryType,
)
from cg.services.order_validation_service.workflows.microsalt.models.sample import (
    MicrosaltSample,
)


class MicrosaltOrder(OrderWithNonHumanSamples):
    delivery_type: MicrosaltDeliveryType
    samples: list[MicrosaltSample]

    @property
    def enumerated_samples(self) -> enumerate[MicrosaltSample]:
        return enumerate(self.samples)