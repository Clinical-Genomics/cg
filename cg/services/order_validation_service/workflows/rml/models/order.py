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
    def pools(self) -> dict[str, dict]:
        """Return a dictionary representation of the order pools, where the dictionary key is the
        pool name and the values are relevant pool attributes."""
        pools: dict[str, dict] = {}
        for sample in self.samples:
            if sample.pool not in pools:
                pool: dict = {
                    "name": sample.pool,
                    "samples": [sample],
                }
                pools[sample.pool] = pool
            else:
                pools[sample.pool]["samples"].append(sample)
        return pools
