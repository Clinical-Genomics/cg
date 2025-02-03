from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.workflows.microsalt.constants import MicrosaltDeliveryType
from cg.services.orders.validation.workflows.microsalt.models.sample import MicrosaltSample


class MicrosaltOrder(OrderWithSamples):
    delivery_type: MicrosaltDeliveryType
    samples: list[MicrosaltSample]

    @property
    def enumerated_samples(self) -> enumerate[MicrosaltSample]:
        return enumerate(self.samples)
