from typing import Generic, TypeVar

from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.sample import Sample

SampleType = TypeVar("SampleType", bound=Sample)


class OrderWithSamples(Order, Generic[SampleType]):
    samples: list[SampleType]

    @property
    def enumerated_samples(self) -> enumerate[SampleType]:
        return enumerate(self.samples)
