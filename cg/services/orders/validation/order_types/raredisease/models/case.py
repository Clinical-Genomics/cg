from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.mip_dna.models.case import MIPDNACase
from cg.services.orders.validation.order_types.raredisease.models.sample import RarediseaseSample

NewSample = Annotated[RarediseaseSample, Tag("new")]
OldSample = Annotated[ExistingSample, Tag("existing")]


class RarediseaseCase(MIPDNACase):
    samples: list[Annotated[NewSample | OldSample, Discriminator(has_internal_id)]]

    def get_samples_with_father(self) -> list[tuple[RarediseaseSample | ExistingSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_samples if sample.father]

    def get_samples_with_mother(self) -> list[tuple[RarediseaseSample | ExistingSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_samples if sample.mother]
