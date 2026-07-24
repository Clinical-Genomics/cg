from typing import Generic, TypeVar

from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.sample import Sample

CaseType = TypeVar("CaseType", bound=Case)
SampleType = TypeVar("SampleType", bound=Sample)


class OrderWithCases(Order, Generic[CaseType, SampleType]):
    cases: list[CaseType]

    @property
    def enumerated_cases(self) -> enumerate[CaseType]:
        return enumerate(self.cases)

    @property
    def enumerated_new_samples(self) -> list[tuple[int, int, SampleType]]:
        return [
            (case_index, sample_index, sample)
            for case_index, case in self.enumerated_cases
            for sample_index, sample in case.enumerated_new_samples
        ]

    @property
    def enumerated_existing_samples(self) -> list[tuple[int, int, ExistingSample]]:
        return [
            (case_index, sample_index, sample)
            for case_index, case in self.enumerated_cases
            for sample_index, sample in case.enumerated_existing_samples
        ]
