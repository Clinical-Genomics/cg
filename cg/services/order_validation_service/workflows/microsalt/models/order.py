from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.microsalt.constants import (
    MicrosaltDeliveryType,
)
from cg.services.order_validation_service.workflows.microsalt.models.sample import (
    MicrosaltSample,
)
from cg.services.order_validation_service.workflows.microsalt.models.sample import (
    MicrosaltSample,
)


class MicrosaltOrder(Order):
    delivery_type: MicrosaltDeliveryType
    samples: list[MicrosaltSample]

    @property
    def enumerated_samples(self) -> enumerate[MicrosaltSample]:
        return enumerate(self.samples)

    @property
    def enumerated_new_samples(self) -> list[tuple[int, MicrosaltSample]]:
        samples: list[tuple[int, MicrosaltSample]] = []
        for sample_index, sample in self.enumerated_samples:
            if sample.is_new:
                samples.append((sample_index, sample))
        return samples
