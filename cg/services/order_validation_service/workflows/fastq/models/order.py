from cg.constants import DataDelivery
from cg.services.order_validation_service.models.order_with_samples import OrderWithNonHumanSamples
from cg.services.order_validation_service.workflows.fastq.models.sample import FastqSample


class FastqOrder(OrderWithNonHumanSamples):
    delivery_type: DataDelivery.FASTQ
    samples: list[FastqSample]
