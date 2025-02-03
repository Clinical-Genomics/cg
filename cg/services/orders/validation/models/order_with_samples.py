from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.sample import Sample


class OrderWithSamples(Order):
    samples: list[Sample]

    @property
    def enumerated_samples(self) -> enumerate[Sample]:
        return enumerate(self.samples)
