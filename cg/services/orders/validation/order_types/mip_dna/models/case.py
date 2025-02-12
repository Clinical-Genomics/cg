from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.mip_dna.models.sample import MIPDNASample

NewSample = Annotated[MIPDNASample, Tag("new")]
OldSample = Annotated[ExistingSample, Tag("existing")]


class MIPDNACase(Case):
    cohorts: list[str] | None = None
    panels: list[str]
    synopsis: str | None = None
    samples: list[Annotated[NewSample | OldSample, Discriminator(has_internal_id)]]

    def get_samples_with_father(self) -> list[tuple[MIPDNASample | ExistingSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_samples if sample.father]

    def get_samples_with_mother(self) -> list[tuple[MIPDNASample | ExistingSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_samples if sample.mother]
