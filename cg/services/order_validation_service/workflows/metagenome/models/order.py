from cg.services.order_validation_service.models.order_with_samples import (
    OrderWithSamples,
)
from cg.services.order_validation_service.workflows.metagenome.constants import (
    MetagenomeDeliveryType,
)
from cg.services.order_validation_service.workflows.metagenome.models.sample import (
    MetagenomeSample,
)


class MicrosaltOrder(OrderWithSamples):
    delivery_type: MetagenomeDeliveryType
    samples: list[MetagenomeSample]

    @property
    def enumerated_samples(self) -> enumerate[MetagenomeSample]:
        return enumerate(self.samples)
