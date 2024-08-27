from pydantic import BaseModel, Discriminator, Field, Tag, model_validator
from typing_extensions import Annotated

from cg.constants.priority import PriorityTerms
from cg.models.orders.sample_base import NAME_PATTERN
from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_sample import ExistingSample
from cg.services.order_validation_service.models.sample import Sample


class Case(BaseModel):
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    priority: PriorityTerms = PriorityTerms.STANDARD
    samples: list[
        Annotated[
            Annotated[Sample, Tag("new")] | Annotated[ExistingSample, Tag("existing")],
            Discriminator(has_internal_id),
        ]
    ]

    @property
    def enumerated_samples(self):
        return enumerate(self.samples)

    @property
    def is_new(self) -> bool:
        return True

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
