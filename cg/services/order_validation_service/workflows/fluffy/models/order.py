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
    def pools(self) -> dict[str, list[FluffySample]]:
        """Return a dictionary matching pool names and their respective samples."""
        pools: dict[str, list[FluffySample]] = {}
        for sample in self.samples:
            if sample.pool not in pools:
                pools[sample.pool] = [sample]
            else:
                pools[sample.pool].append(sample)
        return pools
