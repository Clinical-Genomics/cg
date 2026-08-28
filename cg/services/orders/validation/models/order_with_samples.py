from typing import Generic, TypeVar

from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.sample import Sample
from cg.store.store import Store

SampleType = TypeVar("SampleType", bound=Sample)


class OrderWithSamples(Order, Generic[SampleType]):
    samples: list[SampleType]

    # TODO add tests
    def external_samples(self, status_db: Store) -> list[SampleType]:
        """Expects a validated order."""
        external_samples: list[SampleType] = []
        for sample in self.samples:
            if status_db.get_application_by_tag_strict(sample.application).is_external:
                external_samples.append(sample)
        return external_samples

    @property
    def enumerated_samples(self) -> enumerate[SampleType]:
        return enumerate(self.samples)
