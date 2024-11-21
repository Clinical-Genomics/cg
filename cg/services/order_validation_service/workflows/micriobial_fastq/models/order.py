from cg.services.order_validation_service.models.order_with_samples import OrderWithSamples
from cg.services.order_validation_service.workflows.micriobial_fastq.constants import (
    MicrobialFastqDeliveryType,
)
from cg.services.order_validation_service.workflows.micriobial_fastq.models.sample import (
    MicrobialFastqSample,
)


class MicrobialFastqOrder(OrderWithSamples):
    delivery_type: MicrobialFastqDeliveryType
    samples: list[MicrobialFastqSample]

    @property
    def enumerated_samples(self) -> enumerate[MicrobialFastqSample]:
        return enumerate(self.samples)
