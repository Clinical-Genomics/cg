from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.order_types.rml.constants import RMLDeliveryType
from cg.services.orders.validation.order_types.rml.models.sample import RMLSample


class RMLOrder(OrderWithSamples):
    delivery_type: RMLDeliveryType
    samples: list[RMLSample]

    @property
    def enumerated_samples(self) -> enumerate[RMLSample]:
        return enumerate(self.samples)

    @property
    def pools(self) -> dict[str, list[RMLSample]]:
        """Return a dictionary matching pool names and their respective samples."""
        pools: dict[str, list[RMLSample]] = {}
        for sample in self.samples:
            if sample.pool not in pools:
                pools[sample.pool] = [sample]
            else:
                pools[sample.pool].append(sample)
        return pools

    @property
    def enumerated_pools(self) -> dict[str, list[tuple[int, RMLSample]]]:
        """Return the pool dictionary with indexes for the samples to map them to validation errors."""
        pools: dict[str, list[tuple[int, RMLSample]]] = {}
        for sample_index, sample in self.enumerated_samples:
            if sample.pool not in pools:
                pools[sample.pool] = [(sample_index, sample)]
            else:
                pools[sample.pool].append((sample_index, sample))
        return pools
