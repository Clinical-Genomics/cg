from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.workflows.metagenome.constants import MetagenomeDeliveryType
from cg.services.orders.validation.workflows.metagenome.models.sample import MetagenomeSample


class MetagenomeOrder(OrderWithSamples):
    delivery_type: MetagenomeDeliveryType
    samples: list[MetagenomeSample]

    @property
    def enumerated_samples(self) -> enumerate[MetagenomeSample]:
        return enumerate(self.samples)
