from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.workflows.mutant.constants import MutantDeliveryType
from cg.services.orders.validation.workflows.mutant.models.sample import MutantSample


class MutantOrder(OrderWithSamples):
    delivery_type: MutantDeliveryType
    samples: list[MutantSample]

    @property
    def enumerated_samples(self) -> enumerate[MutantSample]:
        return enumerate(self.samples)
