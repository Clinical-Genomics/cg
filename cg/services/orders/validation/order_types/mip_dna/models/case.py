from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.mip_dna.models.sample import MIPDNASample


class MIPDNACase(Case[MIPDNASample]):
    cohorts: list[str] | None = None
    panels: list[str]
    synopsis: str | None = None

    def get_samples_with_father(self) -> list[tuple[MIPDNASample | ExistingSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_samples if sample.father]

    def get_samples_with_mother(self) -> list[tuple[MIPDNASample | ExistingSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_samples if sample.mother]
