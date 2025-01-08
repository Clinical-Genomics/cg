from cg.constants import Workflow
from cg.services.order_validation_service.models.order_with_samples import OrderWithSamples
from cg.services.order_validation_service.workflows.fluffy.constants import FluffyDeliveryType
from cg.services.order_validation_service.workflows.fluffy.models.sample import FluffySample


class FluffyOrder(OrderWithSamples):
    delivery_type: FluffyDeliveryType
    samples: list[FluffySample]

    @property
    def enumerated_samples(self) -> enumerate[FluffySample]:
        return enumerate(self.samples)

    @property
    def pools_with_samples(self) -> dict[str, dict]:
        """Return a dictionary representation of the order pools, where the dictionary key is the
        pool name and the values are relevant pool attributes."""
        pools: dict[str, dict] = {}
        for sample in self.samples:
            if sample.pool not in pools:
                pool: dict = {
                    "application": sample.application,
                    "data_analysis": Workflow.FLUFFY,
                    "data_delivery": self.delivery_type,
                    "priority": sample.priority,
                    "samples": [sample],
                }
                pools[sample.pool] = pool
            else:
                pools[sample.pool]["samples"].append(sample)
        return pools
