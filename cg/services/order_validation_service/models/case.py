from pydantic import BaseModel, Field, model_validator

from cg.constants.priority import PriorityTerms
from cg.models.orders.sample_base import NAME_PATTERN
from cg.services.order_validation_service.models.sample import Sample


class Case(BaseModel):
    internal_id: str | None = None
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    priority: PriorityTerms = PriorityTerms.STANDARD
    samples: list[Sample]

    @property
    def enumerated_samples(self):
        return enumerate(self.samples)

    @property
    def is_new(self) -> bool:
        return not self.internal_id

    @property
    def enumerated_new_samples(self):
        samples: list[tuple[int, Sample]] = []
        for sample_index, sample in self.enumerated_samples:
            if sample.is_new:
                samples.append((sample_index, sample))
        return samples

    @property
    def enumerated_existing_samples(self) -> list[tuple[int, Sample]]:
        samples: list[tuple[int, Sample]] = []
        for sample_index, sample in self.enumerated_samples:
            if not sample.is_new:
                samples.append((sample_index, sample))
        return samples

    @model_validator(mode="before")
    def convert_empty_strings_to_none(cls, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
        return data
