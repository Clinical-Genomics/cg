from cg.services.order_validation_service.models.aliases import NonHumanSample
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.sample import Sample


class OrderWithNonHumanSamples(Order):
    samples: list[NonHumanSample]

    @property
    def enumerated_samples(self) -> enumerate[NonHumanSample]:
        return enumerate(self.samples)
