from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.order_types.microbial_fastq.constants import (
    MicrobialFastqDeliveryType,
)
from cg.services.orders.validation.order_types.microbial_fastq.models.sample import (
    MicrobialFastqSample,
)


class MicrobialFastqOrder(OrderWithSamples):
    delivery_type: MicrobialFastqDeliveryType
    samples: list[MicrobialFastqSample]

    @property
    def enumerated_samples(self) -> enumerate[MicrobialFastqSample]:
        return enumerate(self.samples)
