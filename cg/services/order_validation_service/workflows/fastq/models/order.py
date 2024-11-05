from cg.services.order_validation_service.models.order_with_samples import OrderWithNonHumanSamples
from cg.services.order_validation_service.workflows.fastq.constants import FastqDeliveryType
from cg.services.order_validation_service.workflows.fastq.models.sample import FastqSample


class FastqOrder(OrderWithNonHumanSamples):
    delivery_type: FastqDeliveryType
    samples: list[FastqSample]
