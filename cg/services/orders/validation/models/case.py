from typing import Generic, TypeVar

from pydantic import BaseModel, Discriminator, Field, Tag, model_validator
from typing_extensions import Annotated

from cg.constants.priority import PriorityTerms
from cg.models.orders.sample_base import NAME_PATTERN
from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.models.sample import Sample
from cg.store.models import Sample as DbSample
from cg.store.store import Store

SampleType = TypeVar("SampleType", bound=Sample)
NewSample = Annotated[SampleType, Tag("new")]
ExistingSampleType = Annotated[ExistingSample, Tag("existing")]


class Case(BaseModel, Generic[SampleType]):
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    priority: PriorityTerms = PriorityTerms.STANDARD
    samples: list[
        Annotated[
            NewSample | ExistingSampleType,
            Discriminator(has_internal_id),
        ]
    ]

    @property
    def is_new(self) -> bool:
        return True

    @property
    def enumerated_samples(self) -> enumerate[NewSample | ExistingSampleType]:
        return enumerate(self.samples)

    @property
    def enumerated_new_samples(self) -> list[tuple[int, SampleType]]:
        samples: list[tuple[int, SampleType]] = []
        for sample_index, sample in self.enumerated_samples:
            if not isinstance(sample, ExistingSample):
                samples.append((sample_index, sample))
        return samples

    @property
    def enumerated_existing_samples(self) -> list[tuple[int, ExistingSample]]:
        samples: list[tuple[int, ExistingSample]] = []
        for sample_index, sample in self.enumerated_samples:
            if isinstance(sample, ExistingSample):
                samples.append((sample_index, sample))
        return samples

    def get_new_sample(self, sample_name: str) -> SampleType | None:
        for _, sample in self.enumerated_new_samples:
            if sample.name == sample_name:
                return sample

    def get_existing_sample_from_db(self, sample_name: str, store: Store) -> DbSample | None:
        for _, sample in self.enumerated_existing_samples:
            db_sample: DbSample | None = store.get_sample_by_internal_id(sample.internal_id)
            if db_sample and db_sample.name == sample_name:
                return db_sample

    @model_validator(mode="before")
    def convert_empty_strings_to_none(cls, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
        return data

    @model_validator(mode="after")
    def set_case_name_on_new_samples(self):
        """Sets the case name on new samples, so it can be easily fetched when stored in LIMS."""
        for _, sample in self.enumerated_new_samples:
            sample._case_name = self.name
        return self

    @model_validator(mode="after")
    def set_case_priority_on_new_samples(self):
        """Sets the priority on new samples, so it can be easily fetched when stored in LIMS."""
        for _, sample in self.enumerated_new_samples:
            sample._case_priority = self.priority
        return self
