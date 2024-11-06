from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.sample import Sample


class OrderWithSamples(Order):
    samples: list[Sample]

    @property
    def enumerated_samples(self) -> enumerate[Sample]:
        return enumerate(self.samples)
