from pydantic import BaseModel, ConfigDict, Field

from cg.constants.constants import DataDelivery
from cg.constants.priority import PriorityTerms
from cg.models.orders.sample_base import NAME_PATTERN
from cg.services.order_validation_service.models.sample import Sample


class Case(BaseModel):
    data_delivery: DataDelivery
    internal_id: str | None = None
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    priority: PriorityTerms = PriorityTerms.STANDARD
    samples: list[Sample]

    model_config = ConfigDict(str_min_length=1)

    @property
    def enumerated_samples(self):
        return enumerate(self.samples)

    @property
    def is_new(self) -> bool:
        return bool(self.internal_id)

    @property
    def enumerated_new_samples(self):
        samples = []
        for sample_index, sample in self.enumerated_samples:
            if sample.is_new:
                samples.append((sample_index, sample))
        return samples
