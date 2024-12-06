from cg.services.order_validation_service.models.order_with_samples import OrderWithSamples
from cg.services.order_validation_service.workflows.pacbio_long_read.constants import (
    PacbioDeliveryType,
)
from cg.services.order_validation_service.workflows.pacbio_long_read.models.sample import (
    PacbioSample,
)


class PacbioOrder(OrderWithSamples):
    delivery_type: PacbioDeliveryType
    samples: list[PacbioSample]

    @property
    def enumerated_samples(self) -> enumerate[PacbioSample]:
        return enumerate(self.samples)
