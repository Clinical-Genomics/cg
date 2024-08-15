from cg.constants import GenePanelMasterList
from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.workflows.tomte.constants import (
    TomteDeliveryType,
)
from cg.services.order_validation_service.workflows.tomte.models.sample import (
    TomteSample,
)


class TomteCase(Case):
    cohorts: list[str] | None = None
    data_delivery: TomteDeliveryType
    panels: list[GenePanelMasterList]
    synopsis: str | None = None
    samples: list[TomteSample]

    def get_sample(self, sample_name: str) -> TomteSample | None:
        for sample in self.samples:
            if sample.name == sample_name:
                return sample

    def get_samples_with_father(self) -> list[tuple[TomteSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_new_samples if sample.father]

    def get_samples_with_mother(self) -> list[tuple[TomteSample, int]]:
        return [(sample, index) for index, sample in self.enumerated_new_samples if sample.mother]
