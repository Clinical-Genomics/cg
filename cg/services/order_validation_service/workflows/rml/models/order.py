from cg.constants import Workflow
from cg.services.order_validation_service.models.order_with_samples import OrderWithSamples
from cg.services.order_validation_service.workflows.rml.constants import RmlDeliveryType
from cg.services.order_validation_service.workflows.rml.models.sample import RmlSample


class RmlOrder(OrderWithSamples):
    delivery_type: RmlDeliveryType
    samples: list[RmlSample]

    @property
    def enumerated_samples(self) -> enumerate[RmlSample]:
        return enumerate(self.samples)

    @property
    def pools(self) -> dict[str, list[RmlSample]]:
        """Return a dictionary matching pool names and their respective samples."""
        pools: dict[str, list[RmlSample]] = {}
        for sample in self.samples:
            if sample.pool not in pools:
                pools[sample.pool] = [sample]
            else:
                pools[sample.pool].append(sample)
        return pools
