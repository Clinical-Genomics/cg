from cg.services.order_validation_service.models.order_with_samples import OrderWithSamples
from cg.services.order_validation_service.workflows.rml.constants import RmlDeliveryType
from cg.services.order_validation_service.workflows.rml.models.sample import RmlSample


class RmlOrder(OrderWithSamples):
    delivery_type: RmlDeliveryType
    samples: list[RmlSample]

    @property
    def enumerated_samples(self) -> enumerate[RmlSample]:
        return enumerate(self.samples)
