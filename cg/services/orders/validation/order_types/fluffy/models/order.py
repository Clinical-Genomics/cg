from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.order_types.fluffy.constants import FluffyDeliveryType
from cg.services.orders.validation.order_types.fluffy.models.sample import FluffySample


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

    @property
    def enumerated_pools(self) -> dict[str, list[tuple[int, FluffySample]]]:
        """Return the pool dictionary with indexes for the samples to map them to validation errors."""
        pools: dict[str, list[tuple[int, FluffySample]]] = {}
        for sample_index, sample in self.enumerated_samples:
            if sample.pool not in pools:
                pools[sample.pool] = [(sample_index, sample)]
            else:
                pools[sample.pool].append((sample_index, sample))
        return pools
