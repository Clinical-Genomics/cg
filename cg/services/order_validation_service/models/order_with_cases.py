from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_case import ExistingCase
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.sample import Sample

NewCaseType = Annotated[Case, Tag("new")]
ExistingCaseType = Annotated[ExistingCase, Tag("existing")]


class OrderWithCases(Order):
    cases: list[Annotated[NewCaseType | ExistingCaseType, Discriminator(has_internal_id)]]

    @property
    def enumerated_cases(self) -> enumerate[Case]:
        return enumerate(self.cases)

    @property
    def enumerated_new_cases(self) -> list[tuple[int, Case]]:
        cases: list[tuple[int, Case]] = []
        for case_index, case in self.enumerated_cases:
            if case.is_new:
                cases.append((case_index, case))
        return cases

    @property
    def enumerated_existing_cases(self) -> list[tuple[int, Case]]:
        cases: list[tuple[int, Case]] = []
        for case_index, case in self.enumerated_cases:
            if not case.is_new:
                cases.append((case_index, case))
        return cases

    @property
    def enumerated_new_samples(self) -> list[tuple[int, int, Sample]]:
        return [
            (case_index, sample_index, sample)
            for case_index, case in self.enumerated_new_cases
            for sample_index, sample in case.enumerated_new_samples
        ]
