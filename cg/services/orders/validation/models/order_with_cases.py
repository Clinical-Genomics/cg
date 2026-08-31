from typing import Generic, TypeVar

from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.sample import Sample
from cg.store.store import Store

CaseType = TypeVar("CaseType", bound=Case)
SampleType = TypeVar("SampleType", bound=Sample)


class OrderWithCases(Order, Generic[CaseType, SampleType]):
    cases: list[
        Annotated[
            Annotated[CaseType, Tag("new")] | Annotated[ExistingCase, Tag("existing")],
            Discriminator(has_internal_id),
        ]
    ]

    def external_samples(self, status_db: Store) -> list[SampleType]:
        external_samples: list[SampleType] = []
        for _, _, sample in self.enumerated_new_samples:
            if status_db.get_application_by_tag_strict(sample.application).is_external:
                external_samples.append(sample)
        return external_samples

    @property
    def enumerated_cases(self) -> enumerate[CaseType | ExistingCase]:
        return enumerate(self.cases)

    @property
    def enumerated_new_cases(self) -> list[tuple[int, CaseType]]:
        cases: list[tuple[int, CaseType]] = []
        for case_index, case in self.enumerated_cases:
            if not isinstance(case, ExistingCase):
                cases.append((case_index, case))
        return cases

    @property
    def enumerated_existing_cases(self) -> list[tuple[int, ExistingCase]]:
        cases: list[tuple[int, ExistingCase]] = []
        for case_index, case in self.enumerated_cases:
            if isinstance(case, ExistingCase):
                cases.append((case_index, case))
        return cases

    @property
    def enumerated_new_samples(self) -> list[tuple[int, int, SampleType]]:
        return [
            (case_index, sample_index, sample)
            for case_index, case in self.enumerated_new_cases
            for sample_index, sample in case.enumerated_new_samples
        ]

    @property
    def enumerated_existing_samples(self) -> list[tuple[int, int, ExistingSample]]:
        return [
            (case_index, sample_index, sample)
            for case_index, case in self.enumerated_new_cases
            for sample_index, sample in case.enumerated_existing_samples
        ]
