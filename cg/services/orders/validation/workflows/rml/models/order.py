from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.workflows.rml.constants import RmlDeliveryType
from cg.services.orders.validation.workflows.rml.models.sample import RmlSample


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

    @property
    def enumerated_pools(self) -> dict[str, list[tuple[int, RmlSample]]]:
        """Return the pool dictionary with indexes for the samples to map them to validation errors."""
        pools: dict[str, list[tuple[int, RmlSample]]] = {}
        for sample_index, sample in self.enumerated_samples:
            if sample.pool not in pools:
                pools[sample.pool] = [(sample_index, sample)]
            else:
                pools[sample.pool].append((sample_index, sample))
        return pools
