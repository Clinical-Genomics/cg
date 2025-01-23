from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.workflows.fastq.constants import FastqDeliveryType
from cg.services.orders.validation.workflows.fastq.models.sample import FastqSample


class FastqOrder(OrderWithSamples):
    delivery_type: FastqDeliveryType
    samples: list[FastqSample]

    @property
    def enumerated_samples(self) -> enumerate[FastqSample]:
        return enumerate(self.samples)
