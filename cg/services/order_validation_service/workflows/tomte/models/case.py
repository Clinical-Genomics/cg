from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_sample import ExistingSample
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample

NewSample = Annotated[TomteSample, Tag("new")]
OldSample = Annotated[ExistingSample, Tag("existing")]


class TomteCase(Case):
    cohorts: list[str] | None = None
    panels: list[str]
    synopsis: str | None = None
    samples: list[Annotated[NewSample | OldSample, Discriminator(has_internal_id)]]

    def get_sample(self, sample_name: str) -> TomteSample | None:
        for sample in self.samples:
            if sample.name == sample_name:
                return sample

    def get_samples_with_father(self) -> list[tuple[TomteSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_samples if sample.father]

    def get_samples_with_mother(self) -> list[tuple[TomteSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_samples if sample.mother]
